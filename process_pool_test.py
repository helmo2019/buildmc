from concurrent.futures import ProcessPoolExecutor, Future, as_completed
from time import sleep

def worker2():
    sleep(5)
    print('finished!')

def main():
    def worker(numbers: list[int]):
        for i in range(len(numbers)):
            print(f'number: {numbers[i]} ({i}/{len(numbers)-1})',flush=True)
            sleep(0.5)

    pool = ProcessPoolExecutor(max_workers=4)
    workers: list[Future] = []

    for _ in range(10):
        workers.append(pool.submit(worker2))

    #for j in range(1, 100, 10):
    #    workers.append(pool.submit(worker, list(range(j, j+10))))
    print(workers)

    for future in as_completed(workers):
        future.result()

if __name__ == '__main__':
    main()