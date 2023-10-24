import asyncio
import json
import httpx


class AsyncApiGithubClient:
    def __init__(self, token):
        self.client = httpx.AsyncClient()
        self.headers = {"Accept": "application/vnd.github.v3+json",
                        "Authorization": f'Bearer {token}'}
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
        ...

    async def _fetch_repos_(self, organization):
        url = f'https://api.github.com/orgs/{organization}/repos'
        response = await self._get_request_(url, {"per_page": 100})
        repos = json.loads(response.content)
        while 'next' in response.links:
            response = await self._get_request_(response.links['next']['url'])
            repos.extend(json.loads(response.content))
        return repos

    async def _fetch_commits_(self, repository):
        url = f'https://api.github.com/repos/skbkontur/{repository}'
        response = await self._get_request_(url)
        return response


async def main():
    organization = 'skbkontur'
    token = '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'
    try:
        client = AsyncApiGithubClient(token)

        task = asyncio.create_task(client._fetch_commits_('markdown'))

        data = await task
        print(data)
    except httpx.HTTPError as err:
        print(f"Ошибка при выполнении запроса: {err}")
    except Exception as err:
        print(f"Произошла ошибка: {err}")


# Запускаем асинхронный цикл событий и выполняем программу
if __name__ == "__main__":
    asyncio.run(main())
