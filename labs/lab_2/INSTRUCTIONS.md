# Инструкция по сборке, запуску и тестированию 
## Windows

Данный документ содержит полное руководство по настройке окружения, компиляции C++ кода, запускным параметрам и автоматическому тестированию Лабораторной работы №1 на операционной системе **Windows**.

---

## 1. Требования к окружению

Для успешной работы в Windows вам понадобятся:
* **Компилятор C++**: MSVC
* **CMake** (версии 3.21 или выше).
* **Python 3.8+** (с добавлением в `PATH`).
* **Ninja**

Так же тесты будут проходить быстрее, если в окружении питона установлен **numpy**.

---

## 2. Главное правило рабочей директории

> **ВАЖНО:** Все команды выполнять в `Developer PowerShell for VS` **строго из корневой папки репозитория** (`Parallel_Programming`), а не из папки `labs/lab_1/`.

Все относительные пути в скриптах и CMake-пресетах завязаны на корень проекта.

## 3. Компиляция проекта CMake

```PowerShell
# 1. Конфигурация проекта
cmake --preset windows-release

# 2. Компиляция
cmake --build --preset windows-release
```
## 4. Запуск C++ программы вручную
Исполняемый файл (`pp_lab_2.exe`) принимает 3 обязательных позиционных аргумента (пути к файлам):

```PowerShell
.\build\windows-release\labs\lab_2\pp_lab_2.exe <путь_к_matrixA> <путь_к_matrixB> <путь_к_matrixC> <число_потоков>
```

Пример прямого запуска:
```PowerShell
.\build\windows-release\labs\lab_2\pp_lab_2.exe labs\lab_2\scripts\matrixA.txt labs\lab_2\scripts\matrixB.txt labs\lab_2\scripts\matrixC_res.txt 8
```

## 5. Автоматизированное тестирование (`PythonMatrixTest.py`)
Для автоматической генерации матриц, запуска бенчмарков и сверки результатов с Python используется скрипт PythonMatrixTest.py.


Запуск тестирования:
```PowerShell
python .\labs\lab_2\scripts\PythonMatrixTest.py
```

## 6. Генерация графиков (`BuildCharts.py`)

```PowerShell
python .\labs\lab_2\scripts\BuildCharts.py
```

Графики в формате .svg будут созданы в папке labs\lab_2\scripts\figures\:
 * omp_time.svg — Время выполнения от размера матрицы $N$ для разного количества потоков.
 * omp_gflops.svg — Производительность (GFLOPS) от размера матрицы.
 * omp_speedup.svg — График ускорения ($S_p$) в зависимости от $N$ и числа потоков.
 * omp_efficiency.svg — График эффективности ($E_p$) распараллеливания.