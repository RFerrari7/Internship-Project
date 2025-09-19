# Internship Project 

This repository contains a project developed as part of the internship carried out between february and may 2025 at the University of Milano Bicocca ([Master's degree in Data Science](https://www.unimib.it/graduate/data-science)).

## Description 
The purpose of this work was to conduct an initial qualitative market analysis through competitor observation and to develop consistent evaluation metrics to support a marketing strategy, with a view to the potential creation of an e-commerce activity in the roller sports sector. The reference point for the definition and categorization of roller sports, as well as for the related equipment, was the official website of the [Italian Roller Sports Federation](fisr.it).
The evaluation metrics for this qualitative market analysis in the roller sports field were based on KPIs (Key Performance Indicators), themselves of a qualitative/descriptive nature, since the reference information for building these metrics was derived from existing online sales websites, with data extracted through web scraping.

The final project pipeline was:
* Step 1: analysis of website structures suitable for the purpose and available resources
* Step 2: development of scripts and fine-tuning of scrapers
* Step 3: weekly data extraction and saving in JSON file format
* Step 4: file storage on MongoDB and aggregation through MongoDB Compass
* Step 5: creation of queries for significant KPIs and graphical representations

## Repository structure

This repository is structured as follows:

```
.
├── KPI_analysis_Deca.ipynb      # python notebook containing KPI analysis on Decathlon data                      
├── KPI_analysis_RS.ipynb        # python notebook containing KPI analysis on Roller Snakes data  
├── Report_stage_eng.pdf         # report in english language
├── Report_stage_ita.pdf         # report in italian language   
├── scraper_Deca.py              # python file containing scraper script for Decathlon website
├── scraper_RollerSnakes.py      # python file containing scraper script for Roller Snakes website          
└── README.md                    
```
