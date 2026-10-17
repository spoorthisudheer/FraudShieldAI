#!/usr/bin/env bash
# FraudShieldAI - Stop Service Script
echo "Stopping FraudShieldAI..."
pkill -f "python.*app.py" 2>/dev/null && echo "FraudShieldAI stopped." || echo "FraudShieldAI was not running."
