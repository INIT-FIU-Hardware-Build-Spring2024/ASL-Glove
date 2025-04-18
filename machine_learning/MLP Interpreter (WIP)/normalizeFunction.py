# normalization function for use with sensor data collection

# normalization formula = (value - minimum value in range)/range of values
# rangeOfValues = range of whatever sensor (flex sensor = 100-800 = range of 700, etc)
# example to normalize flex sensor -> (value of sensor - 100) / 700, 100 would be 0, 800 would be 1

# returns a list with normalized values (all values between 0 and 1)

def normalize(values, minValue, rangeOfValues):
    
    normalizedValues = []
    
    for i in values:
        # adjust round value as desired, will round to x decimal places
        normalizedValues.append(round(((i - minValue)/rangeOfValues), 3)) 
        
    return normalizedValues