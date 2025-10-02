#!/bin/bash
# Lab Data Logging CLI - Example Usage Scripts
# This script demonstrates various ways to use the CLI API

echo "Lab Data Logging CLI - Example Usage"
echo "==================================="

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Activate virtual environment if available
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✓ Virtual environment activated"
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
    echo "✓ Virtual environment activated"
fi

echo ""
echo "Available example commands:"
echo ""

echo "1. Basic test with defaults:"
echo "   python lab_cli.py run-test"
echo ""

echo "2. Quick test (minimal capture):"
echo "   python lab_cli.py run-test --config quick_test_config.yml"
echo ""

echo "3. Comprehensive test (all channels and capture types):"
echo "   python lab_cli.py run-test --config comprehensive_test_config.yml"
echo ""

echo "4. Custom test with command line overrides:"
echo "   python lab_cli.py run-test --board-number TEST001 --label CustomTest --channels CH1 CH2"
echo ""

echo "5. Test with specific VISA address:"
echo '   python lab_cli.py run-test --visa-address "USB0::0x0957::0x17BC::MY56310625::INSTR"'
echo ""

echo "6. List all test results:"
echo "   python lab_cli.py list-results"
echo ""

echo "7. Generate report from existing data:"
echo "   python lab_cli.py generate-report ./captures/00001_Test_20251002.143000"
echo ""

echo "8. Validate configuration file:"
echo "   python lab_cli.py validate-config example_config.yml"
echo ""

echo "9. Show help for any command:"
echo "   python lab_cli.py run-test --help"
echo "   python lab_cli.py list-results --help"
echo "   python lab_cli.py generate-report --help"
echo ""

# Interactive menu
echo "Would you like to run an example? (y/N)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Choose an example to run:"
    echo "1) Validate example configuration"
    echo "2) List existing results"
    echo "3) Quick test (minimal capture)"
    echo "4) Full help display"
    echo "5) Custom test setup"
    echo ""
    echo "Enter choice (1-5): "
    read -r choice
    
    case $choice in
        1)
            echo "Running: python lab_cli.py validate-config example_config.yml"
            python lab_cli.py validate-config example_config.yml
            ;;
        2)
            echo "Running: python lab_cli.py list-results"
            python lab_cli.py list-results
            ;;
        3)
            echo "Running: python lab_cli.py run-test --config quick_test_config.yml"
            echo "This will run a minimal test. Continue? (y/N)"
            read -r confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                python lab_cli.py run-test --config quick_test_config.yml
            fi
            ;;
        4)
            echo "Running: python lab_cli.py --help"
            python lab_cli.py --help
            echo ""
            echo "Running: python lab_cli.py run-test --help"
            python lab_cli.py run-test --help
            ;;
        5)
            echo "Setting up custom test..."
            echo "Enter board number (default: TEST): "
            read -r board_num
            board_num=${board_num:-TEST}
            
            echo "Enter test label (default: Custom): "
            read -r test_label
            test_label=${test_label:-Custom}
            
            echo "Select channels (space-separated, e.g., CH1 CH2 M1): "
            read -r channels
            
            if [ -n "$channels" ]; then
                cmd="python lab_cli.py run-test --board-number $board_num --label $test_label --channels $channels"
            else
                cmd="python lab_cli.py run-test --board-number $board_num --label $test_label"
            fi
            
            echo "Command to run: $cmd"
            echo "Execute this command? (y/N)"
            read -r execute
            if [[ "$execute" =~ ^[Yy]$ ]]; then
                eval $cmd
            fi
            ;;
        *)
            echo "Invalid choice or cancelled."
            ;;
    esac
fi

echo ""
echo "Examples completed. For more options, run:"
echo "python lab_cli.py --help"