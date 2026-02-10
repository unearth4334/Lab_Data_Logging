# Electron App Framework - Submodule Setup Guide

## Overview

The `electron-app-framework` has been extracted as a reusable component that can be shared across multiple projects. This guide explains how to publish it to GitHub and integrate it as a submodule.

## Step 1: Create GitHub Repository

1. Go to GitHub and create a new repository:
   - Name: `electron-app-framework`
   - Description: "Portable Electron application framework with zero-install deployment"
   - Visibility: Public (or Private if you prefer)
   - **Do not** initialize with README (we already have one)

2. Note the repository URL (e.g., `https://github.com/YourUsername/electron-app-framework.git`)

## Step 2: Push Framework to GitHub

```bash
cd "c:\Users\10588\OneDrive - Redlen Technologies\Development\Lab_Data_Logging\electron-app-framework"

# Add the remote
git remote add origin https://github.com/YourUsername/electron-app-framework.git

# Push to GitHub
git push -u origin master
```

## Step 3: Remove Framework from Main Repo

```bash
cd "c:\Users\10588\OneDrive - Redlen Technologies\Development\Lab_Data_Logging"

# Remove the framework directory from git tracking (but keep files for now)
git rm -r --cached electron-app-framework

# Commit the removal
git commit -m "Remove electron-app-framework - preparing for submodule"
```

## Step 4: Add Framework as Submodule

```bash
cd "c:\Users\10588\OneDrive - Redlen Technologies\Development\Lab_Data_Logging"

# Add as submodule
git submodule add https://github.com/YourUsername/electron-app-framework.git electron-app-framework

# Commit the submodule addition
git commit -m "Add electron-app-framework as submodule"
```

## Step 5: Update .gitignore

The main project's `.gitignore` should already be configured, but verify these entries exist:

```gitignore
# Electron app specific
apps/csv_bin_gz_electron/node_modules/
apps/csv_bin_gz_electron/nodejs/

# Framework will be tracked via submodule
# (no need to ignore it)
```

## Using the Framework in Other Projects

Once published, other projects can use the framework:

```bash
# In a new project directory
git submodule add https://github.com/YourUsername/electron-app-framework.git electron-app-framework

# Initialize and update
git submodule update --init --recursive
```

## Updating the Framework

When you make changes to the framework:

```bash
# In the framework directory
cd electron-app-framework
git add -A
git commit -m "Description of changes"
git push origin master

# In the main project
cd ..
git add electron-app-framework
git commit -m "Update electron-app-framework submodule"
git push
```

## Cloning Projects That Use the Framework

When others clone your project:

```bash
# Clone with submodules
git clone --recursive https://github.com/YourUsername/Lab_Data_Logging.git

# Or if already cloned without --recursive
git submodule update --init --recursive
```

## Benefits of This Approach

1. **Reusability**: Use the same framework across multiple Electron projects
2. **Version Control**: Each project can use a specific version/commit of the framework
3. **Separation of Concerns**: Framework updates don't clutter application history
4. **Independent Development**: Framework can be developed and tested independently
5. **Easy Distribution**: Share the framework with other developers/projects

## Alternative: npm Package

If you want even better distribution, consider publishing the framework as an npm package:

```bash
cd electron-app-framework
npm publish
```

Then in your applications:
```bash
npm install electron-app-framework --save
```

This approach is more suitable once the framework API is stable.

## Current Status

✅ Framework extracted to `electron-app-framework/`
✅ Framework initialized as git repository
✅ CSV app refactored to use framework
⏳ Framework needs to be pushed to GitHub
⏳ Submodule needs to be configured

## Next Steps

1. Create GitHub repository for the framework
2. Push framework to GitHub
3. Configure as submodule in main project
4. Test the csv_bin_gz_electron app with the new structure
5. Migrate other apps to use the framework (if applicable)
