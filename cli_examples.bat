@echo off
REM Lab Data Logging CLI - Example Usage Scripts (Windows)
REM This script demonstrates various ways to use the CLI API

echo Lab Data Logging CLI - Example Usage
echo ===================================

REM Change to script directory
cd /d "%~dp0"

REM Activate virtual environment if available
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✓ Virtual environment activated
)

echo.
echo Available example commands:
echo.

echo 1. Basic test with defaults:
echo    python lab_cli.py run-test
echo.

echo 2. Quick test (minimal capture):
echo    python lab_cli.py run-test --config quick_test_config.yml
echo.

echo 3. Comprehensive test (all channels and capture types):
echo    python lab_cli.py run-test --config comprehensive_test_config.yml
echo.

echo 4. Custom test with command line overrides:
echo    python lab_cli.py run-test --board-number TEST001 --label CustomTest --channels CH1 CH2
echo.

echo 5. Test with specific VISA address:
echo    python lab_cli.py run-test --visa-address "USB0::0x0957::0x17BC::MY56310625::INSTR"
echo.

echo 6. List all test results:
echo    python lab_cli.py list-results
echo.

echo 7. Generate report from existing data:
echo    python lab_cli.py generate-report .\captures\00001_Test_20251002.143000
echo.

echo 8. Validate configuration file:
echo    python lab_cli.py validate-config example_config.yml
echo.

echo 9. Show help for any command:
echo    python lab_cli.py run-test --help
echo    python lab_cli.py list-results --help
echo    python lab_cli.py generate-report --help
echo.

REM Interactive menu
set /p response="Would you like to run an example? (y/N): "

if /i "%response%"=="y" (
    echo.
    echo Choose an example to run:
    echo 1^) Validate example configuration
    echo 2^) List existing results
    echo 3^) Quick test ^(minimal capture^)
    echo 4^) Full help display
    echo 5^) Custom test setup
    echo.
    set /p choice="Enter choice (1-5): "
    
    if "!choice!"=="1" (
        echo Running: python lab_cli.py validate-config example_config.yml
        python lab_cli.py validate-config example_config.yml
    ) else if "!choice!"=="2" (
        echo Running: python lab_cli.py list-results
        python lab_cli.py list-results
    ) else if "!choice!"=="3" (
        echo Running: python lab_cli.py run-test --config quick_test_config.yml
        set /p confirm="This will run a minimal test. Continue? (y/N): "
        if /i "!confirm!"=="y" (
            python lab_cli.py run-test --config quick_test_config.yml
        )
    ) else if "!choice!"=="4" (
        echo Running: python lab_cli.py --help
        python lab_cli.py --help
        echo.
        echo Running: python lab_cli.py run-test --help
        python lab_cli.py run-test --help
    ) else if "!choice!"=="5" (
        echo Setting up custom test...
        set /p board_num="Enter board number (default: TEST): "
        if "!board_num!"=="" set board_num=TEST
        
        set /p test_label="Enter test label (default: Custom): "
        if "!test_label!"=="" set test_label=Custom
        
        set /p channels="Select channels (space-separated, e.g., CH1 CH2 M1): "
        
        if not "!channels!"=="" (
            set cmd=python lab_cli.py run-test --board-number !board_num! --label !test_label! --channels !channels!
        ) else (
            set cmd=python lab_cli.py run-test --board-number !board_num! --label !test_label!
        )
        
        echo Command to run: !cmd!
        set /p execute="Execute this command? (y/N): "
        if /i "!execute!"=="y" (
            !cmd!
        )
    ) else (
        echo Invalid choice or cancelled.
    )
)

echo.
echo Examples completed. For more options, run:
echo python lab_cli.py --help

pause