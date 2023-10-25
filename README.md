# Repo-Top

This program is designed to retrieve a list of top contributors from a specific organization using the GitHub API.

## Requirements

- Python 3.6 or above
- `httpx` library

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/repo-top.git
   ```

2. Install the required dependencies:

   ```
   pip install httpx
   ```

## Usage

```
python repo-top.py <token> <organization> [-c <count>] [-t <timeout>]
```

- `<token>`: GitHub access token.
- `<organization>`: GitHub organization. Please specify the name of the organization on the GitHub website.
- `-c <count>` (optional): The number of top contributors in the organization. If it is specified to be greater than the number of actual contributors, it will print exactly the number of contributors available in the organization (default: 100).
- `-t <timeout>` (optional): The timeout for a single request in seconds (default: 15).

Example usage:

```
python repo-top.py your_token your_organization -c 10 -t 30
```
