#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSA3030 Example Usage Script
============================

This script demonstrates basic usage of the RSA3030 spectrum analyzer driver
in the Lab Data Logging framework.

Examples included:
1. Direct connection and identity query
2. Integration with data_logger
3. Connection via IP address
4. Connection via explicit VISA address

For comprehensive testing, use test_rsa3030.py instead.
"""

from libs.RSA3030 import RSA3030
from data_logger import data_logger


def example1_direct_connection():
    """Example 1: Direct connection and identity query"""
    print("\n" + "="*70)
    print("Example 1: Direct Connection")
    print("="*70)
    
    # Auto-connect to RSA3030
    print("\nConnecting to RSA3030...")
    rsa = RSA3030()
    
    # Get instrument identification
    print("\nQuerying instrument identity...")
    identity = rsa.get_identity()
    print(f"Instrument: {identity}")
    
    # Clean up
    rsa.disconnect()
    print("\nExample 1 completed successfully!")


def example2_data_logger_integration():
    """Example 2: Integration with data_logger"""
    print("\n" + "="*70)
    print("Example 2: data_logger Integration")
    print("="*70)
    
    # Initialize logger
    logger = data_logger()
    logger.new_file("rsa3030_example.txt")
    
    # Connect to RSA3030
    print("\nConnecting to RSA3030 via data_logger...")
    rsa = logger.connect("rsa3030")
    
    # Add measurements
    logger.add(rsa, "identity", label="Instrument_ID")
    
    # Collect data
    print("\nCollecting measurement data...")
    logger.get_data()
    
    # Clean up
    logger.close_file()
    rsa.disconnect()
    print("\nExample 2 completed successfully!")


def example3_ip_connection():
    """Example 3: Connect via IP address"""
    print("\n" + "="*70)
    print("Example 3: IP Address Connection")
    print("="*70)
    
    # Connect using IP address
    ip_address = "192.168.1.100"  # Change to your RSA3030 IP
    print(f"\nConnecting to RSA3030 at {ip_address}...")
    
    rsa = RSA3030(ip_address=ip_address)
    identity = rsa.get_identity()
    print(f"Instrument: {identity}")
    
    rsa.disconnect()
    print("\nExample 3 completed successfully!")


def example4_explicit_address():
    """Example 4: Connect via explicit VISA address"""
    print("\n" + "="*70)
    print("Example 4: Explicit VISA Address Connection")
    print("="*70)
    
    # Connect using explicit VISA address
    visa_address = "TCPIP0::192.168.1.100::INSTR"  # Change to your address
    print(f"\nConnecting to RSA3030 at {visa_address}...")
    
    rsa = RSA3030(address=visa_address)
    identity = rsa.get_identity()
    print(f"Instrument: {identity}")
    
    rsa.disconnect()
    print("\nExample 4 completed successfully!")


if __name__ == "__main__":
    print("RSA3030 Spectrum Analyzer - Usage Examples")
    print("=" * 70)
    print("\nNote: These examples require an RSA3030 to be connected.")
    print("Run test_rsa3030.py for comprehensive connectivity testing.")
    print("\nAvailable examples:")
    print("  1. Direct connection and identity query")
    print("  2. Integration with data_logger")
    print("  3. Connection via IP address")
    print("  4. Connection via explicit VISA address")
    
    choice = input("\nSelect example to run (1-4), or 'q' to quit: ").strip()
    
    try:
        if choice == "1":
            example1_direct_connection()
        elif choice == "2":
            example2_data_logger_integration()
        elif choice == "3":
            example3_ip_connection()
        elif choice == "4":
            example4_explicit_address()
        elif choice.lower() == "q":
            print("\nExiting...")
        else:
            print(f"\nInvalid choice: {choice}")
    except ConnectionError as e:
        print(f"\nConnection failed: {e}")
        print("\nTroubleshooting:")
        print("  - Ensure RSA3030 is powered on and connected")
        print("  - Check network connectivity with: ping <IP_ADDRESS>")
        print("  - Run: python test_rsa3030.py --debug")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
