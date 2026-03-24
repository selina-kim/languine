-- PostgreSQL database create tables and add constraints

-- User
create table Users (
    u_id varchar(255) primary key,
    email varchar(255) unique not null,
    display_name varchar(30) not null,
    timezone text not null,
    new_cards_per_day integer default 10, 
    total_due_cards_count integer default 0 not null,
    -- fsrs fields
    desired_retention double precision default 0.9,
    fsrs_parameters double precision[] default null, 
    auto_optimize boolean default true not null,
    num_reviews_per_optimize int default 256 not null, 
    total_reviews int default 0 not null, 
    reviews_since_last_optimize int default 0 not null
);
-- column definitions:
-- u_id: primary key, storing user id from 'sub' field in Google ID Token
-- email: user's email address
-- display_name: user's chosen name to use in app
-- timezone: user's timezone, stored as text (e.g., 'America/New_York')
-- new_cards_per_day: number of new cards user wants to learn per day, default is 10
-- total_due_cards_count: total number of cards currently due for review across all decks, default is 0
    -- Note: for new cards, it will consider a max of new_cards_per_day due per deck. 
-- desired_retention: user's desired card retention rate, default is 0.9 (90%)
-- fsrs_parameters: array to store user's personalized FSRS parameters, default is null (will use default parameters until optimized)
-- auto_optimize: whether to automatically optimize FSRS parameters based on review history, default is true
-- num_reviews_per_optimize: number of reviews after which to run the FSRS optimization, default is 256
-- total_reviews: total number of reviews the user has done, default is 0
-- reviews_since_last_optimize: number of reviews since last optimization, default is 0

-- Deck
create table Decks (
    d_id serial primary key,
    u_id varchar(255) references Users(u_id) on delete cascade, 
    deck_name varchar(100) not null check (deck_name <> ''),
    word_lang varchar(50) not null,
    trans_lang varchar(50) not null,
    creation_date timestamp with time zone default current_timestamp, 
    -- timestamp is stored in UTC. Can be shown in local time based on user's timezone if set. eg. 'Set timezone to "Japan";'
    -- doesn't store timezone info
    last_reviewed timestamp with time zone,
    description text,
    is_public boolean default false not null,
    link varchar(1024),
    due_cards_count integer default 0 not null,
    UNIQUE (u_id, deck_name) -- ensure unique deck names per user
);
-- column definitions:
-- d_id: primary key, storing deck id
-- u_id: foreign key, storing user id of the deck creator
-- deck_name: name of the deck
-- word_lang: language of the words in the deck for learning
-- trans_lang: language the user knows
-- creation_date: date the deck was created
-- last_reviewed: date the deck was last reviewed
-- description: optional description of the deck
-- is_public: whether the deck is public or private, private by default
-- link: link to the deck (if applicable)
-- due_cards_count: number of cards currently due for review in the deck, default is 0
-- index: all decks by user
create index idx_decks_user on Decks(u_id);

-- design choices:
-- store timestamp in UTC to have a standard reference point and then convert to local time using user's timezone

-- Card 
create table Cards (
    c_id serial primary key,
    d_id integer references Decks(d_id) on delete cascade,
    word text not null,
    translation text not null,
    definition text,
    image text,
    word_example text,
    trans_example text,
    word_audio text,
    trans_audio text,
    word_roman text,
    trans_roman text,
    first_reviewed timestamp with time zone default NULL,
    -- FSRS fields: 
    learning_state integer, 
    step integer,
    difficulty double precision,
    stability double precision,
    due_date timestamp with time zone,
    last_review timestamp with time zone,
    successful_reps integer default 0,
    fail_count integer default 0,
    -- ensure fail/success counts are non-negative
    CHECK (successful_reps >= 0),
    CHECK (fail_count >= 0)
);
-- column definitions:
-- c_id: primary key, storing card id
-- word: word the user is learning
-- translation: translation of the word
-- definition: definition of the word
-- image: file path of image for the word stored
-- word_example: example sentence using the word in the language the user is learning
-- trans_example: example sentence using the translation in the user's language
-- word_audio: path to audio for the word stored from API call
-- trans_audio: path to audio for the translation stored from API call
-- word_roman: pronunciation or romanization of the word
-- trans_roman: pronunciation or romanization of the translation
-- first_reviewed: timestamp of the first time the card was reviewed, default is null until the card is reviewed for the first time
    -- this is added to keep track of how many NEW cards have been reviewed today (to calculate how many cards are due)

-- FSRS column definitions:
-- learning_state: current learning state of the card
-- step: current learning or relearning step of the card
-- difficulty: how difficult the card is for the user 
-- stability: how well the memory is retained over time
-- due_date: date the card is due for review
-- last_review: timestamp of the last review of the card
-- successful_reps: number of times the card has been successfully reviewed in row
-- fail_count: number of times the user has failed to recall the card, can be used for leeches

-- index: all cards in a deck
create index idx_cards_deck on Cards(d_id);

-- to store audio we need to store the file in our server and store the link here
-- design choices:
-- We store results from API calls so that we avoid redundant requests,
-- and prevent changes in the result returned over time. This supports the 
-- idea that we help the user generate cards but allow them to make edits.

create table Review_Logs (
    rl_id serial primary key,
    c_id integer references cards(c_id) on delete cascade,
    grade integer not null,      
    review_date timestamp with time zone not null default current_timestamp,
    review_duration integer      
);
-- column definitions:
-- rl_id: primary key, storing review log id
-- c_id: foreign key, storing card id
-- grade: user's self-assessed score of recall quality 
-- review_date: date and time when the review took place
-- review_duration: time taken to recall the card (in milliseconds)

-- index: all review history by card
create index idx_review_logs_card ON Review_Logs(c_id);

-- Insert default test user for development and testing (temporary)
INSERT INTO Users (u_id, email, display_name, timezone)
VALUES ('112255507948077384809', 'languinetest@gmail.com', 'languinetest', 'UTC');
