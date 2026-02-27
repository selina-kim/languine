

Grade
difficulty score (D) - affects the interval growth
retrievability (R)
Stability (S) - the amount of time required for R to decrease from 100% to 90%
    high stability - if a learning consistently recalls information well 
    low stability - if the learner has fluctuating performance - should make more conservative adjustments to prevent drastic changes in intervals
Interval - time in days until the next review
repetitions - number of times the learning has reviewed the item



RETRIEVABILITY
r = 1 + factor * t/s) ** (-w_20)
factor = 0.9 ** (-w_20) - 1

When t = S, R = 90%


INTERVALS
I(DR, S) = S / (0.9 ** (-w_20) -1) * (DR **(-1/w_20) - 1)

I is the interval length
DR is the desired retentiton
When DR is 90%, the interval is equal to stability (S)


STABILITY
S'(D,S,R,G) = S * (1 + w_15 * w_16 * e**w_8 * (11-D) * S **(-w_9) * (e ** (w_10 * (1-R)) -1))

G is grade
S' = (D,S,R) = S * SInc

SInc >= 1; memory stability cannot decrease if the review was successful
Easy, Good, Hard count as success
Again counts as a lapse - use hard as a passing grade
See further details on website https://expertium.github.io/Algorithm.html


w_15 is equal to 1 if the grade is "Good" or "Easy" and is less than 1 if the grade is "Hard"
w_16 is equal to 1 if the grade is "Hard" or "Good" and greater than 1 if the grade is "Easy"


The upgrade formula is different if the user pressed "again"
S' = (D,S,R) = min(w_11 * D ** (-w_12) * ((S + 1) ** w_13 - 1) * e ** (w_14 * (1-R)), S)


First 4 weights are the initial stability values
w_4 corresponds to the easy value



Short-term S
S' = S * e ** (e ** (w_17 * (G - 3 + w_18)) * S ** (-w_19))

Extra check to ensure that S' >= S if G >= 3
Good and Easy cannot decrease S, but Hard and Again
    Different from the main formula... hard cannot decrease S there


Difficulty D
D_0(G) = w_4 - e ** (w_5 * (G-1) + 1)

Again=1, Hard=2, Good=3, Easy=4
0 <= D_0 <= 10

delta_D = -w_6 * (G - 3)

D' = D + delta_D * ((10-D)/9)
D'' = w_7 * D_0(4) + (1 - w_7) * D'


Important takeaway number five: properly defined difficulty must depend on retrievability, not only on grades.



Optimization is done by gradient descent - https://docs.pytorch.org/docs/stable/generated/torch.optim.Adam.html
Choose some initial value for all the parameters (except the first 4)
Change by some small parameter
Check how much the loss function has changed - binary classification with each review being a success or a lapse - binary cross entropy is used
Update the parameters to decrease the loss
Keep updating the parameters (2-4) steps until the loss stops decreasing, which indicates we have reached the minimum

The first 4 parameters are estimated directyl from the results of the first and second reviews and then are further optimized by gradient descent