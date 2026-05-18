# About

This project is called Vision Zero Copilot. It is an early concept for a project with the goal of developing a LLM/AI based system as a copilot for researchers, analysts and investigators at Vision Zero Project of Toronto City. 

# Folder Structure

- datasets: Local-only datasets accumulated so far for this AI application. Each data source is named as the folder name. Folder names are self explanatory. It is usually a json, geojson, csv, or spreadsheet file inside it. Note: This folder does not contain all the data sources this project will need or ingest.
- TRS - Vision Zero AI Copilot.md: This file is an introductory document which has the introducton to TRS, results of brainstorming sessions on this project so far in the form of issues found, enhancements suggested etc. This document should act as a seed document for your work and will be used to come up with the project plan.

# Git Guideline

Right now this project is just placed in a local folder. As soon as we start developmenent work, we must create a git repo locally first and push it on my github account. Every task should be done in a feature branch so its easier to onboard more developers.
- Use Feature branches with story code as a prefix and then task name.
- only create PRs for your features and wait for a human to merge them. Every PR should contain a simple explanation of what the code is doing.
- Do not commit `datasets/` or raw dataset files to git. The `datasets/` folder is local-only and must stay ignored.
- Register dataset metadata, source URLs, schemas, row counts, caveats, and ingest notes in repo-tracked docs/config files instead of committing raw data.
- If a raw dataset was accidentally staged, unstage it and keep only the manifest or documentation changes.
- Long term, raw datasets should move to proper object storage or another approved data store. Git LFS is not the preferred project direction for these files.

# Techstack Guideline
- We do not plan to spend money on infrstructure of pay for any tools.
- We should use open source tools, for infra we will start with local deployments and we have more resource requirements, we will think about free deployment services like vercel or free tiers or cloud like AWS or GCP.
- I am only familiar with python, scala and SQL as programming languages so lets use these. For frontend, you can use the language/framework which is best suited and simplest for our current scope. 
- Do not overcomplicate the architecture. If you do add another service, it should have a genuine and logic backed reasoning behind. For starting we want to keep the architure minimal and as we go on we should add more services to make performance, deployment or dev experience better. 
- Do not wait for me to request enhancements in the architecture. Suggest an improvmeent/refactor in the architecture of this project while working on a specific task.

# General Guidelines
As this project uses open source data and is being developed for a government department, most of the related terms and business specific information should be available public. Use internet to get information to fill any gaps on information that you need. If you do not find authentic and accurate information, then let me know so i can deploy a researcher for that task.
