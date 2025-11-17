# AC215-TarAIntino-Big

--> To update the big repo with potential changes made in the smaller distinct repos
git fetch repo_name (ex. scene_decomposer)
git subtree pull --prefix=repo_name repo_name main -m "chore: subtree pull repo_name"
git push origin main