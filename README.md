# CareConnect Backend

Welcome to the CareConnect Backend repository. This project is the backend service for the CareConnect application, which aims to connect patients with healthcare providers seamlessly.

## Installation

To get started with the CareConnect Backend, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/careconnect-be.git
   ```
2. Navigate to the project directory:
   ```bash
   cd careconnect-be
   ```
3. Create a `config.py` file in the root directory (same location as the `main.py` file) to include the environment variables needed for the server to work properly (ask jay if need help).

4. Setup virtual environment:

   ```bash
   python -m venv .venv
   ```

5. Activate the virtual environment:

   ```bash
   source .venv/bin/activate
   ```

   For windows:

   ```bash
   .venv\Scripts\activate
   ```

   To deactivate (not part of installation):

   ```bash
   deactivate
   ```

6. Install all the requirements:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To start the development server make sure you have python, and run:

```bash
uvicorn main:app --reload
```

## Workflow

See Jira for list of existing issues and to create branches for them.

## Committing Changes

We will be loosely following [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) guideline for our commit messages. See the table below for the list of commit types.

| Type     | Description                                                                           |
| -------- | ------------------------------------------------------------------------------------- |
| feat     | Commits that add a new feature                                                        |
| fix      | Bug fixes                                                                             |
| test     | Addings or changing tests, basically any change within the `test` directory           |
| refactor | Changes to source code that neither add a feature nor fixes a bug                     |
| build    | Changes to CI or build configuration files (Docker, github actions)                   |
| chore    | Anything else that doesn't modify any `src` or `test` files (linters, tsconfig, etc.) |
| revert   | Reverts a previous commit                                                             |

## Contributing

We welcome contributions to the CareConnect Backend project. To contribute, please follow these steps:

1. Create a new branch (`git checkout -b feature-branch`).
2. Make your changes.
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a pull request.
