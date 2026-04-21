# fetch-pr-comments

Fetch unresolved review thread comments from the current branch's PR using `gh`.

Use `gh pr view` to get the PR number and repo, then query with `gh api graphql`:

```graphql
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100) {
        nodes {
          isResolved
          path
          line
          comments(first: 20) {
            nodes {
              author { login }
              body
              url
            }
          }
        }
      }
    }
  }
}
```

Filter to threads where `isResolved == false` and print them. If none, say so.
