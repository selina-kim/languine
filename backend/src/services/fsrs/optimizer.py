"""
services.fsrs.card

Module that defines the Optimizer class.

Ref: https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/optimizer.py
"""

import math
import torch
from random import Random
from copy import deepcopy
from services.fsrs.card import Card
from services.fsrs.grade import Grade
from services.fsrs.review_log import ReviewLog
from services.fsrs.scheduler import Scheduler, DEFAULT_PARAMETERS, LOWER_BOUNDS_PARAMETERS, UPPER_BOUNDS_PARAMETERS
from datetime import datetime, timezone
from pydantic import BaseModel, PrivateAttr, ConfigDict
from torch.nn import BCELoss
from torch import optim
import pandas as pd
from tqdm import tqdm

# weight clipping
LOWER_BOUNDS_PARAMETERS_TENSORS = torch.tensor(LOWER_BOUNDS_PARAMETERS, dtype=torch.float64)
UPPER_BOUNDS_PARAMETERS_TENSORS = torch.tensor(UPPER_BOUNDS_PARAMETERS, dtype=torch.float64)

# hyper parameters
num_epochs = 5
mini_batch_size = 512
learning_rate = 4e-2
max_seq_len = 64  # up to the first 64 reviews of each card are used for optimization


class Optimizer(BaseModel):
    """
    The FSRS optimizer.

    Enables the optimization of FSRS scheduler parameters from existing review logs for more accurate interval calculations.

    Attributes:
        review_logs: A collection of previous ReviewLog objects from a user.
        _revlogs_train: The collection of review logs, sorted and formatted for optimization.
    """
    review_logs: tuple[ReviewLog, ...] | list[ReviewLog]
    _revlogs_train: object = PrivateAttr(default=None)

    model_config = ConfigDict(arbitrary_types_allowed=True)


    def _format_revlogs(self) -> dict:
        """
            Helper Function for model_post_init() that sorts and converts the tuple of ReviewLog objects to a dictionary format for optimizing.

            Returns:
                dict: dictionary of the sorted ReviewLog objects.
        """
        _revlogs_train = {}

        for review_log in self.review_logs:
            card_id = review_log.card_id
            grade = review_log.grade
            review_datetime = review_log.review_datetime
            review_duration = review_log.review_duration

            # if the card was rated Again, it was not recalled
            recall = 0 if grade == Grade.Again else 1

            # as a ML problem, [x, y] = [[review_datetime, grade, review_duration], recall]
            datum = [[review_datetime, grade, review_duration], recall]

            if card_id not in _revlogs_train:
                _revlogs_train[card_id] = []

            _revlogs_train[card_id].append(datum)
            _revlogs_train[card_id] = sorted(_revlogs_train[card_id], key=lambda x: x[0][0])  # keep reviews sorted

        return dict(sorted(_revlogs_train.items())) # sort the dictionary in order of when each card history starts


    def model_post_init(self, __context) -> None:
        self.review_logs = deepcopy(tuple(self.review_logs))
        self._revlogs_train = self._format_revlogs()


    def _compute_batch_loss(self, parameters: list[float]) -> float:
        """
        Computes the current total loss for the entire batch of review logs.

        Args:
            parameters: the current parameters of the model.

        Returns:
            float: the mean loss across the entire batch of review logs.
        """

        card_ids = list(self._revlogs_train.keys())
        params = torch.tensor(parameters, dtype=torch.float64)
        criteron = BCELoss()
        scheduler = Scheduler(parameters=params)
        step_losses = []

        for card_id in card_ids:
            card_review_history = self._revlogs_train[card_id][:max_seq_len]

            for i in range(len(card_review_history)):
                review = card_review_history[i]

                x_date = review[0][0]
                u_grade = review[0][1]
                y_retrievability = review[1]

                if i == 0:
                    card = Card(card_id=card_id, due=x_date) # sets up a fresh card with no learning history at the time of the first review

                y_pred_retrievability = scheduler.get_card_retrievability(card=card, current_datetime=x_date)
                y_retrievability = torch.tensor(y_retrievability, dtype=torch.float64)

                if card.last_review and (x_date - card.last_review).days > 0: # some time must have passed for a review to be meaningful for memory decay
                    step_loss = criteron(y_pred_retrievability, y_retrievability)
                    step_losses.append(step_loss)

                card, _ = scheduler.review_card(card=card, grade=u_grade, review_datetime=x_date, review_duration=None)

        batch_loss = torch.sum(torch.stack(step_losses))
        batch_loss = batch_loss.item() / len(step_losses)

        return batch_loss
    
    def _num_reviews(self) -> int:
        """
        A helper function for compute_optimal_parameters() that computes the number of training steps that correspond to valid "Review"-state memory events.

        This function replays each card's review history using the scheduler in order to reconstruct card's state over time. 
        A review is counted only if it represents a delayed (non-same-day) review, i.e. one for which memory decay applies.

        The resulting count is used to initialize the Cosine Annealing learning rate scheduler with the correct number of optimization steps.

        Returns:
            int: Number of stateful review events used for loss computation.
        """

        scheduler = Scheduler()
        num_reviews = 0
        # iterate through the card review histories
        card_ids = list(self._revlogs_train.keys())
        for card_id in card_ids:
            card_review_history = self._revlogs_train[card_id][:max_seq_len]

            # iterate through the current Card's review history
            for i in range(len(card_review_history)):
                review = card_review_history[i]

                review_datetime = review[0][0]
                grade = review[0][1]

                # if this is the first review, create the Card object
                if i == 0:
                    card = Card(card_id=card_id, due=review_datetime)

                # only non-same-day reviews count
                if (card.last_review and (review_datetime - card.last_review).days > 0):
                    num_reviews += 1

                card, _ = scheduler.review_card(card=card,grade=grade,review_datetime=review_datetime,review_duration=None)

        return num_reviews
    

    def _update_parameters(self, step_losses: list, adam_optimizer: torch.optim.Adam, params: torch.Tensor, lr_scheduler: torch.optim.lr_scheduler.CosineAnnealingLR) -> None:
        """
        A helper function for compute_optimal_parameters() that computes and updates the current FSRS parameters based on the step losses. Also updates the learning rate scheduler.

        Args:
            step_losses: List of loss values for the current mini-batch of reviews.
            adam_optimizer: The Adam optimizer used to update the parameters.
            params: The FSRS scheduler parameters as a PyTorch tensor with gradients enabled.
            lr_scheduler: The cosine annealing learning rate scheduler.
        """

        # Backpropagate through the loss
        mini_batch_loss = torch.sum(torch.stack(step_losses))
        adam_optimizer.zero_grad()  # clear previous gradients
        mini_batch_loss.backward()  # compute gradients
        adam_optimizer.step()  # Update parameters

        # clamp the weights in place without modifying the computational graph
        with torch.no_grad():
            params.clamp_(min=LOWER_BOUNDS_PARAMETERS_TENSORS, max=UPPER_BOUNDS_PARAMETERS_TENSORS)

        # update the learning rate
        lr_scheduler.step()


    def compute_optimal_parameters(self, verbose: bool = False) -> list[float]:
            """
            Computes a set of optimized parameters for the FSRS scheduler and returns it as a list of floats.

            High level explanation of optimization:
            ---------------------------------------
            FSRS is a many-to-many sequence model where the "State" at each step is a Card object at a given point in time,
            the input is the time of the review and the output is the predicted retrievability of the card at the time of review.

            Each card's review history can be thought of as a sequence, each review as a step and each collection of card review histories
            as a batch.

            The loss is computed by comparing the predicted retrievability of the Card at each step with whether the Card was actually
            sucessfully recalled or not (0/1).

            Finally, the card objects at each step in their sequences are updated using the current parameters of the Scheduler
            as well as the grade given to that card by the user. The parameters of the Scheduler is what is being optimized.

            Args:
                verbose: If True, displays a progress bar during optimization. Default is False.

            Returns:
                list[float]: The optimized FSRS scheduler parameters.
            """

            # set local random seed for reproducibility
            rng = Random(42)

            card_ids = list(self._revlogs_train.keys())

            num_reviews = self._num_reviews()

            if num_reviews < mini_batch_size:
                return list(DEFAULT_PARAMETERS)

            # Define FSRS Scheduler parameters as torch tensors with gradients
            params = torch.tensor(DEFAULT_PARAMETERS, requires_grad=True, dtype=torch.float64)

            loss_fn = BCELoss()
            adam_optimizer = optim.Adam([params], lr=learning_rate)
            lr_scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer=adam_optimizer, T_max=math.ceil(num_reviews / mini_batch_size) * num_epochs)

            best_params = None
            best_loss = math.inf
            # iterate through the epochs
            for _ in tqdm(range(num_epochs), desc="Optimizing", unit="epoch", disable=(not verbose)):
                # randomly shuffle the order of which Card's review histories get computed first
                # at the beginning of each new epoch
                rng.shuffle(card_ids)

                # initialize new scheduler with updated parameters each epoch
                scheduler = Scheduler(parameters=params)

                # stores the computed loss of each individual review
                step_losses = []

                # iterate through the card review histories (sequences)
                for card_id in card_ids:
                    card_review_history = self._revlogs_train[card_id][:max_seq_len]

                    # iterate through the current Card's review history (steps)
                    for i in range(len(card_review_history)):
                        review = card_review_history[i]

                        # input
                        x_date = review[0][0]
                        # target
                        y_retrievability = review[1]
                        # update
                        u_grade = review[0][1]

                        # if this is the first review, create the Card object
                        if i == 0:
                            card = Card(card_id=card_id, due=x_date)

                        # predicted target
                        y_pred_retrievability = scheduler.get_card_retrievability(card=card, current_datetime=x_date)
                        y_retrievability = torch.tensor(y_retrievability, dtype=torch.float64)

                        # only compute step-loss on non-same-day reviews
                        if card.last_review and (x_date - card.last_review).days > 0:
                            step_loss = loss_fn(y_pred_retrievability, y_retrievability)
                            step_losses.append(step_loss)

                        # update the card's state
                        card, _ = scheduler.review_card(card=card, grade=u_grade, review_datetime=x_date, review_duration=None)

                        # take a gradient step after each mini-batch
                        if len(step_losses) == mini_batch_size:
                            self._update_parameters(step_losses=step_losses, adam_optimizer=adam_optimizer, params=params, lr_scheduler=lr_scheduler)
                            
                            # Recreate scheduler with updated parameters to reset computational graph
                            scheduler = Scheduler(parameters=params)
                            
                            # clear the step losses for next batch
                            step_losses = []
                            
                            # remove gradient history from tensor card parameters for next batch
                            card.stability = card.stability.detach()
                            card.difficulty = card.difficulty.detach()

                # update params on remaining review logs
                if len(step_losses) > 0:
                    self._update_parameters(step_losses=step_losses, adam_optimizer=adam_optimizer, params=params, lr_scheduler=lr_scheduler)
                    
                # compute the current batch loss after each epoch
                detached_params = [x.detach().item() for x in list(params.detach())]  # convert to floats

                with torch.no_grad():
                    epoch_batch_loss = self._compute_batch_loss(parameters=detached_params)

                # if the batch loss is better with the current parameters, update the current best parameters
                if epoch_batch_loss < best_loss:
                    best_loss = epoch_batch_loss
                    best_params = detached_params

            return best_params if best_params is not None else detached_params


    def _probs_and_means(self, probs_and_costs_dict: dict, sub_df, prefix, normalize_on=None) -> None:
        """
        Computes probability distributions and average review durations for different grades and adds them to probs_and_costs_dict.

        Args:
            probs_and_costs_dict: Dictionary to populate with probability and average duration values.
            sub_df: DataFrame subset containing review logs to analyze.
            prefix: String prefix to add to dictionary keys (e.g., "first" for first reviews).
            normalize_on: Optional list of grade values to normalize probabilities over (e.g., only successful recalls).
        """
        counts = sub_df["grade"].value_counts()
        
        # Calculate total for normalization
        if normalize_on is None:
            total = counts.sum()
        else:
            # Sum counts for grades in normalize_on list
            total = sum(counts.get(grade_val, 0) for grade_val in normalize_on)
        
        # Iterate through all possible grades to ensure all keys are present
        for grade_enum in Grade:
            grade_val = grade_enum.value
            count = counts.get(grade_val, 0)
            
            if normalize_on is None or grade_val in normalize_on:
                # Add prob_ prefix for probabilities
                key = f"prob_{prefix}_{grade_enum.name.lower()}" if prefix else f"prob_{grade_enum.name.lower()}"
                probs_and_costs_dict[key] = (count / total if total else 0)

        means = sub_df.groupby("grade")["review_duration"].mean()
        
        # Ensure all avg_ keys exist, even for grades not in the data
        for grade_enum in Grade:
            grade_val = grade_enum.value
            avg_key = f"avg_{prefix}_{grade_enum.name.lower()}_review_duration" if prefix else f"avg_{grade_enum.name.lower()}_review_duration"
            # Get mean if exists, otherwise default to 0
            probs_and_costs_dict[avg_key] = means.get(grade_val, 0) or 0


    def _compute_probs_and_costs(self) -> dict[str, float]:
        """
        Computes probability distributions and average review durations from review logs for use in retention optimization.

        Returns:
            dict[str, float]: Dictionary containing probabilities (prob_*) and average durations (avg_*) for each grade.
        """
        # Convert review logs to dict format, converting Grade enum to int for pandas
        review_log_dicts = []
        for review_log in self.review_logs:
            log_dict = vars(review_log).copy()
            # Convert Grade enum to int value for pandas operations
            if isinstance(log_dict['grade'], Grade):
                log_dict['grade'] = log_dict['grade'].value
            review_log_dicts.append(log_dict)
        
        review_log_df  = (
            pd.DataFrame(review_log_dicts)
            .sort_values(by=["card_id", "review_datetime"], ascending=[True, True])
            .reset_index(drop=True)
        )

        probs_and_costs_dict = {}

        # first reviews per card
        first_reviews = review_log_df [~review_log_df ["card_id"].duplicated(keep="first")]
        self._probs_and_means(probs_and_costs_dict, first_reviews, "first")

        # non-first reviews
        non_first_reviews = review_log_df [review_log_df ["card_id"].duplicated(keep="first")]

        # probabilities only among successful recalls
        self._probs_and_means(probs_and_costs_dict, non_first_reviews, "", normalize_on=[Grade.Hard.value, Grade.Good.value, Grade.Easy.value])

        return probs_and_costs_dict
    



    def _simulate_cost(self, desired_retention: float, parameters: tuple[float, ...] | list[float], num_cards_simulate: int, probs_and_costs_dict: dict[str, float]) -> float:
        """
        Simulates the cost (total review time) of studying a set of cards over one year with a given retention rate.

        Args:
            desired_retention: Target retention rate (0.0 to 1.0) to simulate.
            parameters: FSRS scheduler parameters to use for scheduling.
            num_cards_simulate: Number of cards to simulate.
            probs_and_costs_dict: Dictionary containing grade probabilities and average review durations.

        Returns:
            float: The simulated cost (total review time divided by total knowledge retained).
        """
        rng = Random(42)

        # simulate from the beginning of 2026 till before the beginning of 2027
        start_date = datetime(2026, 1, 1, 0, 0, 0, 0, timezone.utc)
        end_date = datetime(2027, 1, 1, 0, 0, 0, 0, timezone.utc)

        scheduler = Scheduler(parameters=parameters,desired_retention=desired_retention,enable_fuzzing=False,)

        simulation_cost = 0
        for i in range(num_cards_simulate):
            card = Card()
            curr_date = start_date
            while curr_date < end_date:
                # the card is new
                if curr_date == start_date:
                    grade = rng.choices(
                        [Grade.Again, Grade.Hard, Grade.Good, Grade.Easy],
                        weights=[
                            probs_and_costs_dict["prob_first_again"],
                            probs_and_costs_dict["prob_first_hard"],
                            probs_and_costs_dict["prob_first_good"],
                            probs_and_costs_dict["prob_first_easy"],
                        ],
                    )[0]

                    if grade == Grade.Again:
                        simulation_cost += probs_and_costs_dict["avg_first_again_review_duration"]
                    elif grade == Grade.Hard:
                        simulation_cost += probs_and_costs_dict["avg_first_hard_review_duration"]
                    elif grade == Grade.Good:
                        simulation_cost += probs_and_costs_dict["avg_first_good_review_duration"]
                    elif grade == Grade.Easy:
                        simulation_cost += probs_and_costs_dict["avg_first_easy_review_duration"]
                # the card is not new
                else:
                    grade = rng.choices(["recall", Grade.Again], weights=[desired_retention, 1.0 - desired_retention])[0]

                    if grade == "recall":
                        # compute probability that the user chose hard/good/easy, GIVEN that they correctly recalled the card
                        grade = rng.choices([Grade.Hard, Grade.Good, Grade.Easy], weights=[probs_and_costs_dict["prob_hard"], probs_and_costs_dict["prob_good"], probs_and_costs_dict["prob_easy"]])[0]

                    if grade == Grade.Again:
                        simulation_cost += probs_and_costs_dict["avg_again_review_duration"]
                    elif grade == Grade.Hard:
                        simulation_cost += probs_and_costs_dict["avg_hard_review_duration"]
                    elif grade == Grade.Good:
                        simulation_cost += probs_and_costs_dict["avg_good_review_duration"]
                    elif grade == Grade.Easy:
                        simulation_cost += probs_and_costs_dict["avg_easy_review_duration"]

                card, _ = scheduler.review_card(card=card, grade=grade, review_datetime=curr_date)
                curr_date = card.due

        total_knowledge = desired_retention * num_cards_simulate
        simulation_cost = simulation_cost / total_knowledge

        return simulation_cost


    def _validate_review_logs(self) -> None:
        """
        Helper function for compute_optimal_retention. 
        Validates that all log in review_logs have a review_duration and that the total number of logs is above 512.
        """
        if len(self.review_logs) < 512:
            raise ValueError("Not enough ReviewLog's: at least 512 ReviewLog objects are required to compute optimal retention")

        for review_log in self.review_logs:
            if review_log.review_duration is None:
                raise ValueError("ReviewLog.review_duration cannot be None when computing optimal retention")


    def compute_optimal_retention(self, parameters: tuple[float, ...] | list[float]) -> list[float]:
        """ 
        Simulates different retention targets and selects the target that minimizes the review cost.

        Args:
            parameters: FSRS scheduler parameters to use for simulation.

        Returns:
            float: The optimal retention rate (0.7, 0.75, 0.8, 0.85, 0.9, or 0.95) that minimizes review cost.
        """

        self._validate_review_logs()

        NUM_CARDS_SIMULATE = 1000
        DESIRED_RETENTIONS = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95]

        probs_and_costs_dict = self._compute_probs_and_costs()

        simulation_costs = []
        for desired_retention in DESIRED_RETENTIONS:
            simulation_cost = self._simulate_cost(
                desired_retention=desired_retention,
                parameters=parameters,
                num_cards_simulate=NUM_CARDS_SIMULATE,
                probs_and_costs_dict=probs_and_costs_dict,
            )
            simulation_costs.append(simulation_cost)

        min_index = simulation_costs.index(min(simulation_costs))
        optimal_retention = DESIRED_RETENTIONS[min_index]

        return optimal_retention


    def __str__(self) -> str:
        return self.__repr__()