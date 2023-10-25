import asyncio
import json
import httpx
from collections import Counter


class AsyncApiGithubClient:
    def __init__(self, token):
        self.client = httpx.AsyncClient()
        self.headers = {"Accept": "application/vnd.github.v3+json",
                        "Authorization": f'Bearer {token}',
                        "X-GitHub-Api-Version": "2022-11-28"}
        self.limit = None
        self.remaining = None
        self.used = None

    def _update_rate_limit_(self, response):
        self.limit = int(response.headers['X-RateLimit-Limit'])
        self.remaining = int(response.headers['X-RateLimit-Remaining'])
        self.used = int(response.headers['X-RateLimit-Used'])

    async def _get_request_(self, url, params=None):
        response = await self.client.get(url,
                                         headers=self.headers,
                                         params=params)
        response.raise_for_status()
        self._update_rate_limit_(response)
        return response

    async def fetch_top_committers(self, organization):
        repos = await self._fetch_repos_(organization)

        tasks = []
        for repo_name in (r['full_name'] for r in repos):
            task = self._fetch_commits_(repo_name)
            tasks.append(task)
        repos_commits = await asyncio.gather(*tasks)

        authors = Counter()
        for commits in repos_commits:
            for author in (c['commit']['author']['name'] for c in commits if
                           not c['commit']['message'].startswith(
                               'Merge pull request #')):
                authors[author] += 1
        return authors

    async def _fetch_data_from_pages_(self, url):
        response = await self._get_request_(url, {"per_page": 100})
        data = json.loads(response.content)
        while 'next' in response.links:
            response = await self._get_request_(response.links['next']['url'])
            data.extend(json.loads(response.content))
        return data

    async def _fetch_repos_(self, organization):
        url = f'https://api.github.com/orgs/{organization}/repos'
        return await self._fetch_data_from_pages_(url)

    async def _fetch_commits_(self, repository):
        url = f'https://api.github.com/repos/{repository}/commits'
        return await self._fetch_data_from_pages_(url)


async def main():
    organization = 'skbkontur'
    token = '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'
    try:
        client = AsyncApiGithubClient(token)

        task = asyncio.create_task(
            client.fetch_top_committers(organization))

        data = await task
        print(client.used)
        print(data.total())
        for author, contributions in data.most_common(10000000):
            print(f'{author}: {contributions}')
    except httpx.HTTPError as err:
        print(f"Ошибка при выполнении запроса: {err}")


if __name__ == "__main__":
    asyncio.run(main())
