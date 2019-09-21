# Returns suffix after the last . or empty string
def fileExtension(filename):
    for i in range(len(filename)-1, -1, -1):
        if filename[i] == '.':
            return filename[i+1:len(filename)]
    return ""
