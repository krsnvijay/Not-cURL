from httpc import get_parser, makeRequest
from concurrent.futures import ThreadPoolExecutor

def reset_test_file():
    with open("fs/test.txt", "w") as f:
        f.write("I'm a test file")

parser = get_parser()
read_args = parser.parse_args(["-get", "http://localhost/test.txt", "-v"])
write_args = parser.parse_args(["-post", "http://localhost/test.txt", "-f", "datafile.json", "-v"])
print(read_args)
print(write_args)

reset_test_file()
print("two reads:")
with ThreadPoolExecutor(max_workers=2) as two_reads_executor:
    two_reads_executor.submit(makeRequest, read_args)
    two_reads_executor.submit(makeRequest, read_args)

reset_test_file()
print("two writes:")
with ThreadPoolExecutor(max_workers=2) as two_writes_executor:
    two_writes_executor.submit(makeRequest, write_args)
    two_writes_executor.submit(makeRequest, write_args)

reset_test_file()
print("one read one write:")
with ThreadPoolExecutor(max_workers=2) as one_read_one_write_executor:
    one_read_one_write_executor.submit(makeRequest, read_args)
    one_read_one_write_executor.submit(makeRequest, write_args)

reset_test_file()
print("one write one read:")
with ThreadPoolExecutor(max_workers=2) as one_write_one_read_executor:
    one_write_one_read_executor.submit(makeRequest, write_args)
    one_write_one_read_executor.submit(makeRequest, read_args)
reset_test_file()