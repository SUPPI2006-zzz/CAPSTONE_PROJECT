# Mamaearth Returns & Growth Intelligence Pipeline

Capstone project for the Data Analytics with AI & Gen AI program at E&ICT Academy, IIT Roorkee.

The project answers one question end-to-end: where are returns really coming from, and what is the true revenue picture once the data is cleaned? It is built as three connected layers - a SQL relational store, a Python/pandas analysis layer, and a GenAI narrator - where each layer feeds the next and no layer reports a number it did not compute itself.

## Repository structure

    mamaearth-returns-growth-intelligence/
      README.md
      data/
        customers.csv
        products.csv
        orders.csv
      sql/
        schema.sql
        seed_data.sql
        reports.sql
      analysis/
        clean_and_eda.py
        visualize.py
      visualizations/
        return_rate_by_payment.png
        monthly_revenue_trend.png
      narrator/
        findings.json
        generate_narrative.py
        check_figures.py
        sample_output.txt

## How to run the pipeline

Run everything from the repository root, in this order.

### 1. SQL layer

Load the schema, seed the tables from the CSVs, then run the business reports.

    sqlite3 mamaearth.db ".read sql/schema.sql"
    sqlite3 mamaearth.db ".read sql/seed_data.sql"
    cmd /c "sqlite3 -header -column mamaearth.db < sql\reports.sql"

On macOS or Linux, replace the last line with:

    sqlite3 -header -column mamaearth.db < sql/reports.sql

One note: report (i) uses ALTER TABLE ADD COLUMN, so it will error if the file is run twice against the same database. Delete mamaearth.db and reload it to run the reports again.

### 2. Python analysis layer

    python analysis/clean_and_eda.py
    python analysis/visualize.py

clean_and_eda.py cleans the raw orders data, runs the full EDA, and - at the very end - writes narrator/findings.json. That file is the only source of numbers the narrator is allowed to use. visualize.py regenerates the two charts into visualizations/.

### 3. GenAI narrator layer

With a Gemini API key:

export $env:GEMINI_API_KEY = "your_key_here"
    python narrator/generate_narrative.py

On Windows PowerShell:

   export $env:GEMINI_API_KEY = "your_key_here"
    python narrator/generate_narrative.py

Without a key, the script falls back to an offline template that produces the same three sections using the same numbers:

    python narrator/generate_narrative.py

Either path saves the resulting narrative to narrator/sample_output.txt and prints (path: online, status: success) or (path: offline, status: success).

To verify the narrative contains every required figure:

    python narrator/check_figures.py

## How the layers connect

The SQL layer loads the raw CSVs unchanged and produces the nine reports used to verify the raw numbers. clean_and_eda.py runs an independent pandas pipeline over the same raw CSVs - it does not read from the database - and writes narrator/findings.json. generate_narrative.py reads that JSON and writes the SCR narrative. Every number in the final narrative traces back to findings.json, which traces back to the cleaned data, which traces back to the raw CSVs.