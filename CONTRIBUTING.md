# Contributing to GoldenStat

## Development Workflow

### 1. Create feature branch
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

### 2. Make changes
- Write clean, commented code
- Test your changes locally
- Update documentation if needed

### 3. Commit changes
```bash
git add .
git commit -m "feat: add your feature description

- Detailed change 1
- Detailed change 2

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 4. Push and create PR
```bash
git push -u origin feature/your-feature-name
gh pr create --title "Add your feature" --body "Description of changes"
```

### 5. Code Review
- Wait for automated checks to pass
- Request review if needed
- Address feedback
- Merge when approved

## Commit Message Convention
- `feat:` new features
- `fix:` bug fixes  
- `docs:` documentation changes
- `style:` formatting changes
- `refactor:` code restructuring
- `test:` adding tests
- `chore:` maintenance tasks

## Testing
- Test database operations locally
- Verify API endpoints work
- Check web interface functionality
- Run linting: `flake8 .`