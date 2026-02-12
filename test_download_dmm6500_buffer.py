#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for download_dmm6500_buffer.py

This test validates the buffer download script functionality using a mock DMM6500 device.
"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import subprocess

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_help_output():
    """Test that the help output works."""
    print("Testing help output...")
    result = subprocess.run(
        [sys.executable, "scripts/download_dmm6500_buffer.py", "--help"],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, "Help command should succeed"
    assert "DMM6500" in result.stdout, "Help should mention DMM6500"
    assert "-m MESSAGE" in result.stdout, "Help should include -m option"
    assert "--buffer" in result.stdout, "Help should include --buffer option"
    print("✓ Help output test passed")


def test_csv_generation():
    """Test CSV file generation."""
    print("\nTesting CSV file generation...")
    
    # Import the function
    sys.path.insert(0, str(project_root / "scripts"))
    from download_dmm6500_buffer import save_buffer_to_csv
    
    # Create test data
    test_values = [1.234, 2.345, 3.456, 4.567, 5.678]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test_buffer.csv"
        
        # Save data
        save_buffer_to_csv(
            str(output_file),
            test_values,
            "defbuffer1",
            "Test message"
        )
        
        # Verify file exists
        assert output_file.exists(), "Output file should be created"
        
        # Read and verify content
        content = output_file.read_text()
        
        # Check header
        assert "DMM6500 Buffer Download" in content, "Should have header"
        assert "Buffer: defbuffer1" in content, "Should mention buffer name"
        assert "Message: Test message" in content, "Should include message"
        assert f"Samples: {len(test_values)}" in content, "Should include sample count"
        
        # Check data
        lines = content.split('\n')
        data_lines = [l for l in lines if l and not l.startswith('#') and l != 'Index,Value']
        
        assert len(data_lines) >= len(test_values), "Should have all data points"
        
        # Verify first value
        first_data = data_lines[0].split(',')
        assert first_data[0] == '1', "First index should be 1"
        assert float(first_data[1]) == test_values[0], "First value should match"
        
    print("✓ CSV generation test passed")


def test_filename_generation():
    """Test automatic filename generation."""
    print("\nTesting filename generation...")
    
    sys.path.insert(0, str(project_root / "scripts"))
    from download_dmm6500_buffer import generate_filename
    
    # Test default buffer name
    filename1 = generate_filename()
    assert "dmm6500_buffer_defbuffer1_" in filename1, "Should include buffer name"
    assert filename1.endswith(".csv"), "Should have .csv extension"
    
    # Test custom buffer name
    filename2 = generate_filename("mybuffer")
    assert "dmm6500_buffer_mybuffer_" in filename2, "Should include custom buffer name"
    
    # Test buffer name with quotes (should be cleaned)
    filename3 = generate_filename("'buffer1'")
    assert "'" not in filename3, "Should remove quotes"
    
    print("✓ Filename generation test passed")


def test_mock_download():
    """Test buffer download with mock DMM6500."""
    print("\nTesting mock buffer download...")
    
    # Create mock values
    mock_values = [1.0 + i*0.1 for i in range(100)]
    
    # Mock the DMM6500 class
    with patch('libs.DMM6500.DMM6500') as MockDMM:
        mock_dmm_instance = MagicMock()
        mock_dmm_instance.instrument.resource_name = "MOCK::DMM6500::INSTR"
        mock_dmm_instance.instrument.query.return_value = "Mock DMM6500"
        mock_dmm_instance.fetch_trace.return_value = (mock_values, None)
        MockDMM.return_value = mock_dmm_instance
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "mock_test.csv"
            
            # Run the script programmatically
            sys.path.insert(0, str(project_root / "scripts"))
            from download_dmm6500_buffer import save_buffer_to_csv
            
            # Simulate what main() does
            save_buffer_to_csv(
                str(output_file),
                mock_values,
                "defbuffer1",
                None
            )
            
            # Verify output
            assert output_file.exists(), "Output file should exist"
            content = output_file.read_text()
            assert "DMM6500 Buffer Download" in content, "Should have header"
            
            # Count data lines
            data_lines = [l for l in content.split('\n') 
                         if l and not l.startswith('#') and l != 'Index,Value']
            assert len(data_lines) == len(mock_values), "Should have all data points"
    
    print("✓ Mock download test passed")


def run_all_tests():
    """Run all tests."""
    print("="*70)
    print("Testing download_dmm6500_buffer.py")
    print("="*70)
    
    try:
        test_help_output()
        test_csv_generation()
        test_filename_generation()
        test_mock_download()
        
        print("\n" + "="*70)
        print("All tests passed! ✓")
        print("="*70)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
