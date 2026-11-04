
$ErrorActionPreference = "Stop"

Write-Host "Setting up Smart Attendance System..."

# Check Python 3.12
py -3.12 --version
if ($LASTEXITCODE -ne 0) {
    throw "Install Python 3.12 before continuing."
}

# Create virtual environment
if (-not (Test-Path ".venv312\Scripts\python.exe")) {
    py -3.12 -m venv .venv312
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create virtual environment."
    }
}

$python = ".\.venv312\Scripts\python.exe"

# Install dependencies
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }

& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

# Initialize database
& $python database.py
if ($LASTEXITCODE -ne 0) { throw "Database setup failed." }

Write-Host ""
Write-Host "Setup complete!"
Write-Host "Next: Create an admin account with:"
Write-Host "$python setup_admin.py"
Write-Host "Then start the website with:"
Write-Host "$python dashboard/app.py"
