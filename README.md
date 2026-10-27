# Inventory AI Agent - EECE 430 Assignment 5

## Build and run

Open a terminal in the main project folder. Create a local `.env` file using `.env.example` and set your `GEMINI_API_KEY`.

```powershell
docker build --load -t inventory-agent .
docker run -d --name inventory-agent -p 8000:8000 --env-file .env inventory-agent
```

Open http://localhost:8000. The image starts with an empty inventory database. Add items through the agent.

## Run from GitHub

```powershell
git clone https://github.com/theanamansour/EECE430-LAB5-TheanaMansour.git
cd EECE430-LAB5-TheanaMansour
```

Create `.env` with your Gemini API key, then run the build and run commands above.

