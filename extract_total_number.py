# %%
#CODE CHALLENGE DAY 1

# %%
input_data = [
    "mul(4,5)",   # Valid operation
    "add(3,2)",   # Invalid operation
    "mul(2,9)",   # Valid operation
    "sub(1,4)",   # Invalid operation
    "mul(10,3)",  # Valid operation
    "mul(3,abc)", # Invalid due to non-numeric argument
    "div(6,2)",   # Invalid operation
    "mul(7,8)",   # Valid operation
    "mul(-2,6)"   # Valid operation
]


# %%
def extract_total_number(data):
    total_sum = 0 

    for line in data:

        if line.startswith("mul(") and line.endswith(")"):
            try:
                inner_content = line[4:-1] # Remove "mul(" and ")"
                x,y = map(int, inner_content.split(","))  #Split by comma and convert to integers

                total_sum += x*y
            except(ValueError, IndexError):
                # If parsing fails or the format is incorrect, skip the line
                continue

    return total_sum        

# %%
result = extract_total_number(input_data)


# %%
print(f"Result of the input data is {result}")

# %%


# %%


# %%



