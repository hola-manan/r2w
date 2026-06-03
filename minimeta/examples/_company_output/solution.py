def tip_total(bill: float, tip_percent: float) -> float:
  """
  Calculates the total bill amount including a specified tip percentage.

  Args:
    bill: The original bill amount (float).
    tip_percent: The tip percentage to be applied (e.g., 15 for 15%) (float).

  Returns:
    The total bill amount including the calculated tip (float).
  """
  tip_amount = bill * (tip_percent / 100)
  total = bill + tip_amount
  return total

if __name__ == '__main__':
  # Test case 1: Standard tip
  bill1 = 100.00
  tip_percent1 = 15.0
  expected_total1 = 115.00
  calculated_total1 = tip_total(bill1, tip_percent1)
  assert abs(calculated_total1 - expected_total1) < 1e-9, f"Test Case 1 Failed: Expected {expected_total1}, Got {calculated_total1}"
  print(f"Test Case 1 Passed: bill={bill1}, tip_percent={tip_percent1}, total={calculated_total1}")

  # Test case 2: Zero tip
  bill2 = 50.00
  tip_percent2 = 0.0
  expected_total2 = 50.00
  calculated_total2 = tip_total(bill2, tip_percent2)
  assert abs(calculated_total2 - expected_total2) < 1e-9, f"Test Case 2 Failed: Expected {expected_total2}, Got {calculated_total2}"
  print(f"Test Case 2 Passed: bill={bill2}, tip_percent={tip_percent2}, total={calculated_total2}")

  # Test case 3: Higher tip percentage
  bill3 = 75.50
  tip_percent3 = 20.0
  expected_total3 = 75.50 + (75.50 * 0.20)
  calculated_total3 = tip_total(bill3, tip_percent3)
  assert abs(calculated_total3 - expected_total3) < 1e-9, f"Test Case 3 Failed: Expected {expected_total3}, Got {calculated_total3}"
  print(f"Test Case 3 Passed: bill={bill3}, tip_percent={tip_percent3}, total={calculated_total3}")

  # Test case 4: Zero bill
  bill4 = 0.00
  tip_percent4 = 10.0
  expected_total4 = 0.00
  calculated_total4 = tip_total(bill4, tip_percent4)
  assert abs(calculated_total4 - expected_total4) < 1e-9, f"Test Case 4 Failed: Expected {expected_total4}, Got {calculated_total4}"
  print(f"Test Case 4 Passed: bill={bill4}, tip_percent={tip_percent4}, total={calculated_total4}")

  # Test case 5: Decimal bill and tip percentage
  bill5 = 123.45
  tip_percent5 = 18.75
  expected_total5 = 123.45 + (123.45 * (18.75 / 100))
  calculated_total5 = tip_total(bill5, tip_percent5)
  assert abs(calculated_total5 - expected_total5) < 1e-9, f"Test Case 5 Failed: Expected {expected_total5}, Got {calculated_total5}"
  print(f"Test Case 5 Passed: bill={bill5}, tip_percent={tip_percent5}, total={calculated_total5}")
