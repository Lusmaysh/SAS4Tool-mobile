## How to Release

1. Make sure `main` has the changes you want to ship.
2. Tag it: `git tag vX.Y.Z`
3. Push the tag: `git push origin vX.Y.Z`
4. GitHub Actions will build the exe and attach it to a new Release automatically.
