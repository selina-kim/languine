-- PostgreSQL database create tables and add constraints

-- User
create table Users (
    u_id varchar(255) primary key,
    email varchar(255) unique not null,
    display_name varchar(30) not null,
    timezone varchar(50) not null,
    new_cards_per_day integer default 20,
    review_cards_per_day integer default 50
);
-- column definitions:
-- u_id: primary key, storing user id from 'sub' field in Google ID Token
-- email: user's email address
-- display_name: user's chosen name to use in app
-- new_cards_per_day: number of new cards user wants to learn per day, default is 20
-- review_cards_per_day: number of cards user wants to review per day, default is 50

-- Deck
create table Decks (
    d_id serial primary key,
    u_id varchar(255) references Users(u_id) on delete cascade, 
    deck_name varchar(100) not null,
    word_lang varchar(50) not null,
    trans_lang varchar(50) not null,
    creation_date timestamp with time zone default current_timestamp, 
    -- timestamp is stored in UTC. Can be shown in local time based on user's timezone if set. eg. 'Set timezone to "Japan";'
    -- doesn't store timezone info
    last_reviewed timestamp with time zone,
    description text,
    is_public boolean default false not null,
    link varchar(3000)
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

-- design choices:
-- store timestamp in UTC to have a standard reference point and then convert to local time using user's timezone

-- Card 
create table Cards (
    c_id serial primary key,
    d_id integer references Decks(d_id) on delete cascade,
    word varchar(100) not null,
    translation varchar(100) not null,
    definition text not null,
    image text,
    word_example text not null,
    trans_example text,
    word_audio varchar(255),
    trans_audio varchar(255),
    word_roman varchar(100) not null,
    trans_roman varchar(100)
);
-- to store audio we need to store the file in our server and store the link here

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


-- design choices:
-- We store results from API calls so that we avoid redundant requests,
-- and prevent changes in the result returned over time. This supports the 
-- idea that we help the user generate cards but allow them to make edits.


-- Card Review based on FSRS
create table Review (
    r_id serial primary key,
    c_id integer unique references Cards(c_id) on delete cascade,
    last_review_date timestamp with time zone,
    interval integer not null,
    due_date timestamp with time zone,
    successful_reps integer default 0,
    fail_count integer default 0,
    recall_time integer,
    difficulty double precision,
    stability double precision,
    retrievability double precision,
    is_due boolean default false
);  
-- column definitions:
-- r_id: primary key, storing card review id
-- c_id: foreign key, storing card id?
-- last_review_date: date the card was last reviewed
-- interval: number of days until next review
-- due_date: date the card is due for review
-- successful_reps: number of times the card has been successfully reviewed in row
-- fail_count: number of times the user has failed to recall the card
-- recall_time: how long it took the user to recall the card during last review (in seconds)
-- difficulty: how difficult the card is for the user 
-- stability: how well the memory is retained over time
-- retrievability: how easily the user can retrieve the card from memory
-- is_due: boolean indicating if the card is due for review today

-- additional constraints
-- Ensure email format (basic check for x@y.z)
ALTER TABLE Users
ADD CONSTRAINT chk_email_format CHECK (email ~* '^[^@]+@[^@]+\\.[^@]+$');


-- Ensure unique deck names per user
ALTER TABLE Decks
ADD CONSTRAINT unique_deck_per_user UNIQUE (u_id, deck_name);


-- Ensure due_date >= last_review when both present
ALTER TABLE Review
ADD CONSTRAINT chk_review_dates CHECK (
    due_date IS NULL OR last_review_date IS NULL OR due_date >= last_review_date
);

-- Ensure that the fail/success counts intervals are non-negative
ALTER TABLE Review
ADD CONSTRAINT nonnegative_counts CHECK (successful_reps >= 0 AND fail_count >= 0 and interval >= 0);
