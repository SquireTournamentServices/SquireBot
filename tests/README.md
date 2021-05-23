## Introduction

This directory contains the unit tests for SquireBot.
After the tester bot has been set up, it can be used in conjugtion with the `testingBot` found at the base of this project.
The tester bot doesn't monitor the output from the testing bot.
Rather, it responds when it sees a message from the testing bot, so you will have to look through the output to ensure the test passed.
If an error occurs in the testing bot, it will likely not send a message.
This will stop the test.
Running the test again will start it from the top.



## Setup
Like SquireBot, an `.env` file is used by the tester bot.
That file needs three things, the Discord token for the bot called `TESTER_TOKEN`, and the IDs of SquireBot and the testing bot called `SquireBotID` and `PrototypeBotID` respectively.
In Discord, the tester bot will need the "Tournament Admin" role.
If you have SquireBot in the your server, it is best to have a testing channel that SquireBot can't see.
This channel should be visible to the testing and tester bots.


## Using the Bot
Start by running both the tester and testing bots.
To run all the tests, simply run the `!run-tests` command.
To see what tests are available, run the `!view-tests` command.
The `!run-tests` command takes any number of arguments, which can be the names of tests.


