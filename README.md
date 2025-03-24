I started thinking about how to create a simple program to calculate the work card of the company where I work. I had started thinking about the realization through Access but, given the difficulties in managing negative hours and minutes (which are also not managed in Excel) I said to myself: why not use AI to create it with Python?

So I started asking ChatGPT for help in this regard first, and Copilot present here.

Unfortunately, I was not able to have a streamlined code that is functional, given the numerous parameters that are applied for the calculation of missing hours, overtime and various types of reasons that exist for the correct calculation of the time card.

In the end, I managed to have a code that reads a csv file and processes it to have an output file, always in csv, but with the data organized by working days and for causals, which also takes into account multiple stamps during the day.

All this because the report that is delivered at the end of the month, reports - in my opinion - inconsistencies that are due to an incorrect entry and management of the data necessary for the correct calculation.

In the repository I uploaded the stamping file, a settings file with the explanation for the calculations and the last two working versions that Copilot generated according to my instructions.

