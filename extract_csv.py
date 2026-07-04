import pandas as pd
import json
import csv
import argparse
import re
import html

def clean_html(text):
    """
    Удаляет HTML-теги, HTML-сущности и шорткоды типа @@...@@
    """
    if not isinstance(text, str):
        return text
   
    text = html.unescape(text)
    text = re.sub(r'@@[^@]+@@', '', text)
    text = re.sub(r'\n', '', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_answer_json(json_str):
    """
    Извлекает:
    - вопрос (html) – очищенный
    - для input id=1: correctAnswer, userAnswer, right, wrong, errors
    - для input id=2: correctAnswer, userAnswer, right, wrong, errors
    - общую статистику: automaticScore, totalScore, teacherScore
    """
    try:
        data = json.loads(json_str)
    except Exception as e:
        print(f"Ошибка парсинга JSON: {e}")
        return {}

    result = {}

    stats = data.get('statistic', {})
    result['automaticScore'] = stats.get('automaticScore', '')
    result['totalScore'] = stats.get('totalScore', '')
    result['teacherScore'] = stats.get('teacherScore', '')

    # Ищем subtask 
    subtasks = data.get('subtasks', [])
    subtask = next((s for s in subtasks if str(s.get('id')) == '1'), None)
    if not subtask:
        subtask = subtasks[0] if subtasks else None

    if subtask:
        raw_question = subtask.get('html', '')
        result['question'] = clean_html(raw_question)
    else:
        result['question'] = ''

    # Функции для извлечения данных из input
    def get_correct(input_item):
        if not input_item:
            return ''
        ca = input_item.get('correctAnswer')
        if isinstance(ca, list):
            return '; '.join(str(x) for x in ca)
        elif ca is not None:
            return str(ca)
        return ''

    def get_user_answer(input_item):
        if not input_item:
            return ''
        ua = input_item.get('userAnswer')
        if not ua:
            return ''
        if isinstance(ua, str):
            try:
                ua_obj = json.loads(ua)
                raw = ua_obj.get('actualHtml', ua_obj.get('localValue', ''))
                return clean_html(raw)
            except:
                return clean_html(ua)
        elif isinstance(ua, dict):
            raw = ua.get('actualHtml', ua.get('localValue', ''))
            return clean_html(raw)
        else:
            return clean_html(str(ua))

    def get_stats(input_item, key):
        if not input_item:
            return ''
        stat = input_item.get('statistic', {})
        return stat.get(key, '')

    # Ищем inputs внутри subtask
    if subtask:
        inputs = subtask.get('inputs', [])
        input1 = next((inp for inp in inputs if str(inp.get('id')) == '1'), None)
        input2 = next((inp for inp in inputs if str(inp.get('id')) == '2'), None)

        # Input 1
        result['correctAnswer_1'] = clean_html(get_correct(input1))
        result['userAnswer_1'] = get_user_answer(input1)
        result['right_1'] = get_stats(input1, 'right')
        result['wrong_1'] = get_stats(input1, 'wrong')
        result['errors_1'] = get_stats(input1, 'errors')

        # Input 2
        result['correctAnswer_2'] = get_correct(input2)
        result['userAnswer_2'] = get_user_answer(input2)
        result['right_2'] = get_stats(input2, 'right')
        result['wrong_2'] = get_stats(input2, 'wrong')
        result['errors_2'] = get_stats(input2, 'errors')
    else:
        result['correctAnswer_1'] = ''
        result['userAnswer_1'] = ''
        result['right_1'] = ''
        result['wrong_1'] = ''
        result['errors_1'] = ''
        result['correctAnswer_2'] = ''
        result['userAnswer_2'] = ''
        result['right_2'] = ''
        result['wrong_2'] = ''
        result['errors_2'] = ''

    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='Путь к входному CSV')
    parser.add_argument('output', help='Путь для выходного CSV')
    parser.add_argument('--encoding', default='utf-8', help='Кодировка')
    args = parser.parse_args()

    # Определение разделителя
    with open(args.input, 'r', encoding=args.encoding) as f:
        sample = f.read(2048)
    for delim in [';', ',', '\t']:
        if 'task_id' in sample and delim in sample:
            used_delim = delim
            break
    else:
        used_delim = ';'
    #print(f"Используемый разделитель: {repr(used_delim)}")

    with open(args.input, 'r', encoding=args.encoding) as f:
        lines = f.readlines()
    header_idx = None
    for i, line in enumerate(lines):
        parts = [p.strip().lower() for p in line.split(used_delim)]
        if 'task_id' in parts and 'answer' in parts:
            header_idx = i
            break
    if header_idx is None:
        print("Не найден заголовок с 'task_id' и 'answer'. Используем первую строку.")
        header_idx = 0
    header = [p.strip() for p in lines[header_idx].split(used_delim)]
    #print(f"Заголовок: {header}")

    rows = []
    with open(args.input, 'r', encoding=args.encoding) as f:
        reader = csv.reader(f, delimiter=used_delim, quotechar='"')
        for i, row in enumerate(reader):
            if i < header_idx:
                continue
            if i == header_idx:
                continue
            if row and any(row):
                rows.append(row)
    #print(f"Прочитано строк: {len(rows)}")

    if not rows:
        print("Нет данных для обработки.")
        return

    df = pd.DataFrame(rows, columns=header)
    #print("Колонки DataFrame:", df.columns.tolist())

    if 'answer' not in df.columns:
        #print("Ошибка: колонка 'answer' не найдена.")
        return

    parsed = df['answer'].apply(parse_answer_json).apply(pd.Series)

    #print("Первые строки parsed (пример):")
    #print(parsed.head())

    if 'student_id' not in df.columns:
        #print("Ошибка: колонка 'student_id' не найдена.")
        return

    result_df = pd.concat([
        df[['student_id']],
        parsed[['question',
                'correctAnswer_1', 'userAnswer_1', 'right_1', 'wrong_1', 'errors_1',
                'correctAnswer_2', 'userAnswer_2', 'right_2', 'wrong_2', 'errors_2',
                'automaticScore', 'totalScore', 'teacherScore']]
    ], axis=1)

    result_df.to_csv(args.output, index=False, encoding='utf-8')
    print(f"Файл {args.output} создан.")
    print(f"Обработано строк: {len(result_df)}")


if __name__ == '__main__':
    main()