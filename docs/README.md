# TwisterLab Documentation

## Overview

TwisterLab is a cloud-native, multi-agent AI infrastructure designed to facilitate complex tasks through autonomous agents. Built on a robust architecture using Python and FastAPI, TwisterLab leverages the Model Context Protocol (MCP) to enable seamless interaction between agents.

## Key Features

- **Autonomous Agents**: TwisterLab consists of a swarm of AI agents that collaborate to perform various tasks such as monitoring, backups, and incident resolution.
- **Cloud-Native Architecture**: The system is designed for deployment on Kubernetes, emphasizing automation, monitoring, and CI/CD practices.
- **MCP Integration**: Full Model Context Protocol support for IDE integration (Claude Desktop, Continue).
- **Flexible Operation Modes**: The system can operate in real, hybrid, or mock modes, showcasing its maturity in design for development and testing.

## Getting Started

To get started with TwisterLab, follow these steps:

1. **Clone the Repository**:
   ```
   git clone https://github.com/yourusername/TwisterLab.git
   cd TwisterLab
   ```

2. **Set Up Environment**:
   Create a `.env` file based on the `.env.example` provided in the repository and fill in the necessary environment variables.

3. **Install Dependencies**:
   Use Poetry or pip to install the required dependencies:
   ```
   poetry install
   # or
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   Start the FastAPI application:
   ```
   python -m uvicorn src.twisterlab.api.main:app --reload --port 8000
   ```

5. **Access the API**:
   Open your browser and navigate to `http://localhost:8000/docs` to access the interactive API documentation.

## Directory Structure

- **src/twisterlab**: Contains the main application code, including API routes and agents.
- **deploy/k8s**: Contains Kubernetes manifests for deploying the application.
- **docs**: Documentation files for the project.
- **tests**: Unit tests for the application components.
- **scripts**: Utility scripts for scaffolding and logging.
- **scaffold**: Contains templates for creating new agents.

## Contributing

Contributions are welcome! Please follow the standard GitHub workflow for submitting issues and pull requests. Ensure that your code adheres to the project's coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
