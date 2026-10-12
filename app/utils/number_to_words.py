def _two_digits(n: int) -> str:
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    if n < 20:
        return ones[n]
    else:
        tens_part = tens[n // 10]
        ones_part = ones[n % 10]
        return f"{tens_part} {ones_part}".strip()

def _three_digits(n: int) -> str:
    hundreds = n // 100
    rem = n % 100
    res = []
    if hundreds > 0:
        res.append(f"{_two_digits(hundreds)} Hundred")
    if rem > 0:
        res.append(_two_digits(rem))
    return " ".join(res)

def indian_number_to_words(amount: float) -> str:
    """
    Converts a number into Indian currency words representation.
    e.g. 58500.00 -> "Rupees Fifty Eight Thousand Five Hundred Only."
    1195000.00 -> "Rupees Eleven Lakh Ninety Five Thousand Only."
    """
    if amount < 0:
        return "Negative " + indian_number_to_words(-amount)
    
    # Separate integer and decimal part
    rounded = round(amount, 2)
    rupees = int(rounded)
    paise = int(round((rounded - rupees) * 100))
    
    if rupees == 0 and paise == 0:
        return "Rupees Zero Only."
    
    parts = []
    
    # Crores (10,000,000)
    crores = rupees // 10000000
    rupees %= 10000000
    if crores > 0:
        parts.append(f"{indian_number_to_words(crores).replace('Rupees ', '').replace(' Only.', '')} Crore")
    
    # Lakhs (100,000)
    lakhs = rupees // 100000
    rupees %= 100000
    if lakhs > 0:
        parts.append(f"{_two_digits(lakhs)} Lakh")
    
    # Thousands (1,000)
    thousands = rupees // 1000
    rupees %= 1000
    if thousands > 0:
        parts.append(f"{_two_digits(thousands)} Thousand")
    
    # Hundreds & Remainder
    if rupees > 0:
        parts.append(_three_digits(rupees))
    
    rupees_str = " ".join(parts).strip()
    if not rupees_str:
        rupees_str = "Zero"
        
    result = f"Rupees {rupees_str}"
    
    if paise > 0:
        paise_str = _two_digits(paise)
        result += f" and {paise_str} Paise"
        
    result += " Only."
    return result

if __name__ == "__main__":
    print(indian_number_to_words(58500.00))
    print(indian_number_to_words(1195000.00))
    print(indian_number_to_words(55714.28))
