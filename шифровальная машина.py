import json
import os
import re

# ===== АЛФАВИТ =====
ALPHABET = (
    "0123456789"
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
    " .,!?:;–()[]{}+-=*%^√&#@|/\\_`'°∆$~"
)
N = len(ALPHABET)
ALPHA_INDEX = {c: i for i, c in enumerate(ALPHABET)}

# ===== ФАЙЛ ПРОТОКОЛОВ =====
PROTOCOLS_FILE = "protocols.json"

def load_protocols():
    if not os.path.exists(PROTOCOLS_FILE):
        return {}
    
    try:
        with open(PROTOCOLS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        print("\n" + "*"*35)
        print("⚠️ Неправильный формат файла protocols.json")
        print("Файл содержит некорректные данные.")
        print("1 – удалить файл и создать новый")
        print("0 – выйти из программы")
        choice = input("> ").strip()
        if choice == "1":
            os.remove(PROTOCOLS_FILE)
            return {}
        else:
            exit(0)
    
    if not isinstance(data, dict):
        print("\n" + "*"*35)
        print("⚠️ Неправильный формат файла protocols.json")
        print("Ожидался словарь, получен", type(data).__name__)
        print("1 – удалить файл и создать новый")
        print("0 – выйти из программы")
        choice = input("> ").strip()
        if choice == "1":
            os.remove(PROTOCOLS_FILE)
            return {}
        else:
            exit(0)
    
    corrupted = []
    valid = {}
    for name, proto in data.items():
        if not isinstance(name, str) or not isinstance(proto, str):
            corrupted.append(f"{name}: {proto}")
        else:
            valid[name] = proto
    
    if corrupted:
        print("\n" + "*"*35)
        print("⚠️ В файле protocols.json найдены повреждённые записи:")
        for item in corrupted:
            print(f"  {item}")
        print("\n1 – удалить повреждённые записи")
        print("2 – оставить как есть (возможны ошибки)")
        print("0 – выйти из программы")
        choice = input("> ").strip()
        if choice == "1":
            save_protocols(valid)
            return valid
        elif choice == "0":
            exit(0)
    
    return data

def save_protocols(protocols):
    with open(PROTOCOLS_FILE, 'w', encoding='utf-8') as f:
        json.dump(protocols, f, indent=2, ensure_ascii=False)

# ===== ОСНОВНЫЕ ФУНКЦИИ =====
def apply_shift(text, shift):
    result = []
    for c in text:
        if c not in ALPHA_INDEX:
            raise ValueError(f"Недопустимый символ: {c}")
        new_idx = (ALPHA_INDEX[c] + shift) % N
        result.append(ALPHABET[new_idx])
    return "".join(result)

def apply_mirror(text, block_size):
    if block_size <= 0:
        raise ValueError("Размер блока должен быть положительным")
    result = []
    for i in range(0, len(text), block_size):
        result.append(text[i:i + block_size][::-1])
    return "".join(result)

def apply_linear_with_mode(text, k_str, mode="encrypt"):
    if k_str.startswith('*'):
        k_str = '0.' + k_str[1:]
    elif k_str.startswith('-*'):
        k_str = '-0.' + k_str[2:]
    try:
        K = float(k_str)
    except ValueError:
        raise ValueError(f"Некорректный коэффициент для линейной функции: {k_str}")
    result = []
    for i, c in enumerate(text):
        if c not in ALPHA_INDEX:
            raise ValueError(f"Недопустимый символ: {c}")
        raw_shift = K * (i + 1)
        shift = int(round(raw_shift))
        if mode == "decrypt":
            shift = -shift
        new_idx = (ALPHA_INDEX[c] + shift) % N
        result.append(ALPHABET[new_idx])
    return "".join(result)

def apply_wave(text, height, mode="encrypt"):
    """Волна с правильной обратимостью"""
    if height == 0:
        return text
    
    H = abs(height)
    
    # Базовая последовательность для положительной высоты
    base_inc = []
    for i in range(H, 0, -1):
        base_inc.append(i)
    for i in range(1, H + 1):
        base_inc.append(-i)
    
    # Полная последовательность для положительной волны
    pos_inc = base_inc + [-x for x in base_inc]
    
    # Определяем последовательность в зависимости от режима и знака
    if mode == "decrypt":
        increments = [-x for x in pos_inc]
    else:
        increments = pos_inc
    
    # Если исходная высота отрицательная — инвертируем
    if height < 0:
        increments = [-x for x in increments]
    
    result = []
    current = 0
    for i, c in enumerate(text):
        if c not in ALPHA_INDEX:
            raise ValueError(f"Недопустимый символ: {c}")
        new_idx = (ALPHA_INDEX[c] + current) % N
        result.append(ALPHABET[new_idx])
        current += increments[i % len(increments)]
    
    return "".join(result)

# ===== ПРОВЕРКА ЦЕЛЫХ ЧИСЕЛ =====
def is_integer(s):
    s = s.strip()
    if s.startswith('-'):
        s = s[1:]
    return s.isdigit()

# ===== ПРОТОКОЛ =====
def process_protocol(protocol, text, mode):
    commands = []
    i = 0
    while i < len(protocol):
        cmd = protocol[i]
        if cmd not in ('p', 'm', 'l', 'w'):
            raise ValueError(f"❌ Неизвестная команда: {cmd}")
        i += 1
        
        param = ""
        while i < len(protocol) and protocol[i] not in ('p', 'm', 'l', 'w'):
            param += protocol[i]
            i += 1
        
        if not param:
            raise ValueError(f"❌ Нет параметра для команды {cmd}")
        
        commands.append((cmd, param))
    
    if mode == "decrypt":
        commands = commands[::-1]
    
    for cmd, param in commands:
        if cmd == 'p':
            if not is_integer(param):
                raise ValueError(f"❌ Команда p должна содержать целое число (получено: {param})")
            shift = int(param)
            if mode == "decrypt":
                shift = -shift
            text = apply_shift(text, shift)
        elif cmd == 'm':
            if not is_integer(param):
                raise ValueError(f"❌ Команда m должна содержать целое число (получено: {param})")
            text = apply_mirror(text, int(param))
        elif cmd == 'l':
            text = apply_linear_with_mode(text, param, mode)
        elif cmd == 'w':
            if not is_integer(param):
                raise ValueError(f"❌ Команда w должна содержать целое число (получено: {param})")
            height = int(param)
            text = apply_wave(text, height, mode)
    
    return text

# ===== ПРОВЕРКА ПРОТОКОЛА =====
def check_protocol(protocol, original_text):
    try:
        encrypted = process_protocol(protocol, original_text, "encrypt")
        decrypted = process_protocol(protocol, encrypted, "decrypt")
        return (decrypted == original_text), encrypted, decrypted
    except Exception as e:
        return False, None, str(e)

# ===== ПАРСИНГ КОМАНДЫ =====
def parse_command(data, protocols):
    data = data.strip()
    if data.startswith('#'):
        parts = data[1:].split('/', 1)
        if len(parts) != 2:
            return None, None, "Используйте формат: #имя/текст"
        name, text = parts
        if name not in protocols:
            return None, None, f"❌ Протокол \"{name}\" не найден."
        return protocols[name], text, None
    else:
        if '/' not in data:
            return None, None, "Ошибка: используйте формат протокол/текст"
        protocol, text = data.split('/', 1)
        return protocol, text, None

# ===== УПРАВЛЕНИЕ ПРОТОКОЛАМИ =====
def show_protocols_list(protocols):
    if not protocols:
        print("\nУ вас нет готовых протоколов.\n")
        return False
    items = list(protocols.items())
    print("\nВаши протоколы:")
    for idx, (name, proto) in enumerate(items, 1):
        print(f"{idx}. {name}/{proto}")
    print()
    return True

def add_protocol(protocols):
    while True:
        entry = input("Введите шаблон в формате название/протокол: ").strip()
        if entry.count('/') != 1:
            print("🚫 Неверный формат! Должен быть ровно один символ /")
            print("Пример: D3@ф7/p37l0.7m3l*3")
            continue
        
        name, proto = entry.split('/', 1)
        
        if not name:
            print("🚫 Название не может быть пустым.")
            continue
        
        if not proto:
            print("🚫 Протокол не может быть пустым.")
            continue
        
        if name in protocols:
            print(f"⚠️ Протокол с именем \"{name}\" уже существует.")
            print("1 – заменить существующий")
            print("2 – ввести другое имя")
            print("0 – отмена")
            choice = input("> ").strip()
            if choice == "1":
                protocols[name] = proto
                save_protocols(protocols)
                print(f"✅ Сохранён как \"{name}\"")
                print("//////////////////////////////////////////////////")
                return
            elif choice == "2":
                continue
            else:
                return
        else:
            protocols[name] = proto
            save_protocols(protocols)
            print(f"✅ Сохранён как \"{name}\"")
            print("//////////////////////////////////////////////////")
            return

def edit_protocol(protocols):
    if not show_protocols_list(protocols):
        return
    items = list(protocols.items())
    choice = input("Введите номер протокола для изменения: ").strip()
    if not choice.isdigit():
        return
    idx = int(choice) - 1
    if idx < 0 or idx >= len(items):
        return
    old_name, old_proto = items[idx]
    print(f"Редактирование: {old_name}/{old_proto}")
    
    entry = input("Введите новый шаблон название/протокол: ").strip()
    if entry.count('/') != 1:
        print("🚫 Неверный формат! Должен быть ровно один символ /")
        return
    
    name, proto = entry.split('/', 1)
    
    if not name:
        print("🚫 Название не может быть пустым.")
        return
    
    if not proto:
        print("🚫 Протокол не может быть пустым.")
        return
    
    if name != old_name and name in protocols:
        print(f"⚠️ Протокол с именем \"{name}\" уже существует.")
        print("1 – заменить существующий")
        print("2 – ввести другое имя")
        print("0 – отмена")
        subchoice = input("> ").strip()
        if subchoice == "1":
            protocols[name] = proto
            if name != old_name:
                del protocols[old_name]
            save_protocols(protocols)
            print("✅ Протокол изменён.")
            print("//////////////////////////////////////////////////")
        return
    
    protocols[name] = proto
    if name != old_name:
        del protocols[old_name]
    save_protocols(protocols)
    print("✅ Протокол изменён.")
    print("//////////////////////////////////////////////////")

def delete_protocols(protocols):
    if not show_protocols_list(protocols):
        return
    choice = input("Введите номер(а) протокола(ов) (через пробел) (! – удалить все, 0 – назад): ").strip()
    if choice == "0":
        return
    items = list(protocols.items())
    if choice == "!":
        print("Вы точно хотите удалить ВСЕ протоколы?")
        print("1 – удалить")
        print("0 – вернуться")
        if input("> ").strip() == "1":
            protocols.clear()
            save_protocols(protocols)
            print("✅ Протоколы успешно удалены.")
            print("//////////////////////////////////////////////////")
        return
    indices = []
    names_to_delete = []
    display_names = []
    for part in choice.split():
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(items):
                indices.append(idx)
                name, proto = items[idx]
                names_to_delete.append(name)
                display_names.append(f"{name}/{proto}")
    if not names_to_delete:
        return
    print(f"Вы точно хотите удалить следующие шаблоны: {'; '.join(display_names)}?")
    print("1 – удалить")
    print("0 – вернуться")
    if input("> ").strip() == "1":
        for name in names_to_delete:
            if name in protocols:
                del protocols[name]
        save_protocols(protocols)
        print("✅ Протоколы успешно удалены.")
        print("//////////////////////////////////////////////////")

def protocols_menu(protocols):
    while True:
        if protocols:
            show_protocols_list(protocols)
            print("1 – добавить протокол")
            print("2 – изменить протокол")
            print("3 – удалить протоколы")
            print("4 – скопировать протокол")
            print("0 – назад")
        else:
            print("У вас нет готовых протоколов.\n")
            print("1 – добавить протокол")
            print("0 – назад")
        choice = input("> ").strip()
        if choice == "0":
            break
        elif choice == "1":
            add_protocol(protocols)
        elif choice == "2":
            edit_protocol(protocols)
        elif choice == "3":
            delete_protocols(protocols)
        elif choice == "4":
            print("⏳ Функция будет доступна позже.")
        else:
            print("Неизвестная команда.")

# ===== ИНСТРУКЦИЯ =====
def show_instruction():
    print("\n" + "="*35)
    print("ИНСТРУКЦИЯ ПО РАБОТЕ С ПРОТОКОЛАМИ")
    print("="*35)
    print("\nПротокол — это ключ для шифрования и расшифровки сообщений,")
    print("использующий комбинации из функций, показанных ниже.")
    print("\n" + "-"*35)
    print("ФОРМАТ ПРОТОКОЛА:")
    print("-"*35)
    print("  [функция1][параметр][функция2][параметр]... / текст")
    print("\n  Параметры указываются сразу после функции без пробелов.")
    print("  Функции применяются последовательно слева направо.")
    print("\n" + "-"*35)
    print("ДОСТУПНЫЕ ФУНКЦИИ:")
    print("-"*35)
    print("  pN   – сдвиг на N символов по алфавиту")
    print("         N – целое число (может быть отрицательным)")
    print("  mN   – зеркальное отражение блоков размера N")
    print("         N – целое положительное число")
    print("  lK   – изменение смещения по линейной функции")
    print("         K – целое или дробное число (*5 = 0.5)")
    print("  wA   – изменения по волне с увеличением или уменьшением")
    print("         размера сдвига от -A до A")
    print("         A – целое число (положительное или отрицательное)")
    print("\n" + "-"*35)
    print("ПРИМЕРЫ ПРОТОКОЛОВ:")
    print("-"*35)
    print("  p3m2/12345")
    print("  l*5p2/hello")
    print("  w3p2/Привет")
    print("  m5w-2/Тест")
    print("\n" + "-"*35)
    print("ИСПОЛЬЗОВАНИЕ СОХРАНЁННЫХ ПРОТОКОЛОВ:")
    print("-"*35)
    print("  #имя/текст – применить сохранённый протокол")
    print("  Пример: #base32/Привет")
    print("\n  Сохранить протокол можно в меню 4.")
    print("\n" + "="*35)
    input("Нажмите Enter для продолжения...")

# ===== ГЛАВНЫЙ ЦИКЛ =====
def main():
    protocols = load_protocols()
    while True:
        print("\n" + "="*40)
        print("CUSTOM CYPHER PROTOCOL SYSTEM (CCPS)")
        print("V1.0")
        print("Безопасность не даётся — она создаётся.")
        print("Создай свой шифр.")
        print("="*40)
        print("Сделано Dendr0_0")
        print("="*40)
        print("1 – зашифровать")
        print("2 – расшифровать")
        print("3 – проверить работу")
        print("4 – управление готовыми протоколами")
        print("0 – выход")
        choice = input("> ").strip()
        if choice == "0":
            break
        elif choice == "4":
            protocols_menu(protocols)
            continue
        elif choice not in ("1", "2", "3"):
            print("Неизвестная команда.")
            continue
        while True:
            data = input("Введите команду (i – инструкция, 0 – главное меню): ").strip()
            if data == "0":
                break
            if data.lower() == "i":
                show_instruction()
                continue
            protocol, text, error = parse_command(data, protocols)
            if error:
                print(error)
                continue
            try:
                if choice == "3":
                    is_ok, encrypted, decrypted = check_protocol(protocol, text)
                    if encrypted is None:
                        print(f"\n{protocol}/{decrypted}")
                        print("⚠️ОШИБКА В ПРОТОКОЛЕ!⚠️")
                    else:
                        print()
                        i = 0
                        parts = []
                        while i < len(protocol):
                            cmd = protocol[i]
                            i += 1
                            param = ""
                            while i < len(protocol) and protocol[i] not in ('p','m','l','w'):
                                param += protocol[i]
                                i += 1
                            if cmd == 'p':
                                parts.append(f"place({param})")
                            elif cmd == 'm':
                                parts.append(f"mirror({param})")
                            elif cmd == 'l':
                                parts.append(f"linear({param})")
                            elif cmd == 'w':
                                parts.append(f"wave({param})")
                        print(f"протокол: {' '.join(parts)}")
                        print(f"ввод: {text}")
                        print(f"вывод: {encrypted}")
                        print(f"расшифровка: {decrypted}")
                        if is_ok:
                            print("✅ ФУНКЦИЯ КОРРЕКТНА")
                        else:
                            print("❌ ОШИБКА ФУНКЦИИ")
                            print("⚠️ СООБЩИТЕ ВЛАДЕЛЬЦУ")
                else:
                    mode = "encrypt" if choice == "1" else "decrypt"
                    result = process_protocol(protocol, text, mode)
                    if data.startswith('#'):
                        name = data[1:].split('/', 1)[0]
                        print(f"\nПротокол: {protocols[name]} ({name})")
                        print(f"Результат: {result}")
                    else:
                        print(f"\n{protocol}/{result}")
                    
                    if choice == "1":
                        check = process_protocol(protocol, result, "decrypt")
                        if check == text:
                            print("\n-----ошибок не обнаружено-----")
                        else:
                            print("\n⚠️ОШИБКА! ОБНАРУЖЕНО НЕСОВПАДЕНИЕ!⚠️")
                            print("проверьте работу функции в главном меню (3)")
            except Exception as e:
                print(f"\n⚠️ Ошибка: {e}")
            input("\nНажмите Enter для продолжения...")
            break

if __name__ == "__main__":
    main()
