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
Исполняемый файл (`pp_lab_1.exe`) принимает 3 обязательных позиционных аргумента (пути к файлам):

```PowerShell
.\build\windows-release\labs\lab_1\pp_lab_1.exe <путь_к_matrixA> <путь_к_matrixB> <путь_к_matrixC>
```

Пример прямого запуска:
```PowerShell
.\build\windows-release\labs\lab_1\pp_lab_1.exe labs\lab_1\matrixA.txt labs\lab_1\matrixB.txt labs\lab_1\matrixC_res.txt
```

## 5. Автоматизированное тестирование (`PythonMatrixTest.py`)
Для автоматической генерации матриц, запуска бенчмарков и сверки результатов с Python используется скрипт PythonMatrixTest.py.


Запуск тестирования:
```PowerShell
python .\labs\lab_1\scripts\PythonMatrixTest.py
```

## 6. Генерация графиков (`BuildCharts.py`)

```PowerShell
python .\labs\lab_1\scripts\BuildCharts.py
```

Графики в формате .svg будут созданы в папке labs\lab_1\scripts\figures\:
 * time_by_size.svg — График времени выполнения в линейном масштабе.
 * time_by_size_log.svg — График времени в логарифмической шкале ($\log_{10}$).
 * throughput_by_size.svg — График производительности (GFLOPS).