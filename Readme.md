This is my submission to the Teiko Technical exam. 

Each of these scripts cover each parts of the exam:
- load_data.py - Part 1: Data management
- part2.py - Part 2: Initial Analysis - Data Overview
- part3. py - Part 3: Statistical Analysis
- part4. py - Part 4 Data Subset Analysis: 
- check.py was just a short script I wrote to double check that the data was loaded correctly.
- dashboard.py - this combines all work from all parts and initializes the local server for my interactive dashboard using Flask.

The Makefile in the root directory runs through each parts then runs the dashboard script. This line can be run on Terminal:
```python
make setup && make pipeline && make dashboard
```
Then ctrl+click on the link after "Running on" to open the dashboard running on port 5000.
Thank you!

Sally (Nahyun) Kim
nsallykim@gmail.com