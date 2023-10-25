import argparse
import asyncio
import json
import httpx
import requests
from collections import Counter


class RateLimitError(Exception):
    ...


class AsyncGithubApiClient:
    rate_limit_url = 'https://api.github.com/rate_limit'

    def __init__(self, token, timeout=15):
        self.client = httpx.AsyncClient(timeout=timeout)
        self.headers = {"Accept": "application/vnd.github.v3+json",
                        "Authorization": f'Bearer {token}',
                        "X-GitHub-Api-Version": "2022-11-28"}
        self.timeout = timeout

        rate_limit_data = json.loads(requests.get(
            AsyncGithubApiClient.rate_limit_url,
            headers=self.headers,
            timeout=self.timeout).content)
        self.limit = rate_limit_data['resources']['core']['limit']
        self.remaining = rate_limit_data['resources']['core']['remaining']
        self.used = rate_limit_data['resources']['core']['used']

    async def async_get_request(self, url, params=None):
        if self.remaining == 0:
            raise RateLimitError('Rate limit exceeded')
        response = await self.client.get(url,
                                         headers=self.headers,
                                         params=params)
        response.raise_for_status()
        self._update_rate_limit_(response)
        return response

    def _update_rate_limit_(self, response):
        self.limit = int(response.headers['X-RateLimit-Limit'])
        self.remaining = int(response.headers['X-RateLimit-Remaining'])
        self.used = int(response.headers['X-RateLimit-Used'])

    async def fetch_top_committers(self, organization, top_count=100):
        repos = await self._fetch_repos_(organization)

        repos_commits = await self._fetch_repos_commits(repos)

        authors = Counter()
        for commits in repos_commits:
            for author in (c['commit']['author']['email'] for c in commits if
                           not c['commit']['message'].startswith(
                               'Merge pull request #')):
                authors[author] += 1

        return authors.most_common(top_count)

    async def _fetch_repos_commits(self, repos):
        tasks = []
        for repo_name in (r['full_name'] for r in repos if r['size'] > 0):
            task = self._fetch_commits_(repo_name)
            tasks.append(task)
        return await asyncio.gather(*tasks)

    async def _fetch_data_from_pages_(self, url):
        response = await self.async_get_request(url, {"per_page": 100})
        data = json.loads(response.content)
        while 'next' in response.links:
            response = await self.async_get_request(
                response.links['next']['url'])
            data.extend(json.loads(response.content))
        return data

    async def _fetch_repos_(self, organization):
        url = f'https://api.github.com/orgs/{organization}/repos'
        return await self._fetch_data_from_pages_(url)

    async def _fetch_commits_(self, repository):
        url = f'https://api.github.com/repos/{repository}/commits'
        return await self._fetch_data_from_pages_(url)


async def main(args):
    token = args.token
    organization = args.organization
    try:
        client = AsyncGithubApiClient(token, args.t)

        task = asyncio.create_task(
            client.fetch_top_committers(organization, args.c))

        data = await task
        print(
            f'You have been used {client.used} queries of {client.limit}. Remaining: {client.remaining}')
        print()
        for author, contributions in data:
            print(f'{author}: {contributions} commits count')

    except httpx.HTTPStatusError as err:
        print(f"Ошибка при выполнении запроса: {err}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='repo-top',
                                     description='This program is designed to retrieve a list of top contributors from a specific organization using the GitHub API.')
    parser.add_argument('token', type=str,
                        help='Github access token')
    parser.add_argument('organization', type=str,
                        help='Github organization. Please specify the name of the organization on the Github website.')
    parser.add_argument('-c', default=100, type=int,
                        help='The number of top contributors in the organization. If it is specified to be greater than the number of actual contributors, it will print exactly the number of contributors available in the organization.')
    parser.add_argument('-t', default=15, type=float,
                        help='The timeout for a single request in seconds')
    args = parser.parse_args()
    asyncio.run(main(args))
