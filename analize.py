import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.signal import savgol_filter
from openpyxl import load_workbook


# ---------- 0. Подготовка папки ----------
os.makedirs("output", exist_ok=True)


# ---------- 1. Чтение ----------
# sep=';'    — разделитель в файле — точка с запятой
# na_values  — пропуски в данных UCI закодированы символом '?'
df = pd.read_csv(
    "data/household_power_consumption 2006-2007.txt",
    sep=";",
    na_values=["?"],
    low_memory=False,
)
print("Прочитано строк:", len(df))
print(df.head())


# ---------- 2. Склеиваем дату и время ----------
df["datetime"] = pd.to_datetime(
    df["Date"] + " " + df["Time"], format="%d/%m/%Y %H:%M:%S"
)
df = df.drop(columns=["Date", "Time"])


# ---------- 3. Приводим всё к числам ----------
for col in df.columns.drop("datetime"):
    df[col] = pd.to_numeric(df[col], errors="coerce")


# ---------- 4. Выкидываем строки без активной мощности ----------
df = df.dropna(subset=["Global_active_power"])
df = df.sort_values("datetime").reset_index(drop=True)


# ---------- 5. Энергия за каждую минуту, кВт·ч ----------
# мощность [кВт] * 1/60 [ч] = энергия [кВт·ч]
df["energy_kwh"] = df["Global_active_power"] * (1 / 60)


# ---------- 6. Суточная сумма ----------
daily = df.groupby(df["datetime"].dt.date)["energy_kwh"].sum()
print("\nСуточное энергопотребление, кВт·ч:")
print(daily)


# ---------- 7. Статистика ----------
mean = np.mean(daily.values)
std = np.std(daily.values)
print(f"\nСреднее по дням: {mean:.2f} кВт·ч, std: {std:.2f}")


# ---------- 8. Excel — ДЕЛАЕМ ДО ГРАФИКОВ ----------
xlsx_path = "output/daily_energy.xlsx"
daily.to_frame("energy_kwh").to_excel(xlsx_path)

wb = load_workbook(xlsx_path)
ws = wb.active
ws.column_dimensions["A"].width = 15
ws.column_dimensions["B"].width = 15
wb.save(xlsx_path)
print("Excel сохранён:", os.path.abspath(xlsx_path))


# ---------- 9. ГРАФИК 1: суточная энергия — ЛИНИЯ ----------
daily_dt = pd.to_datetime(daily.index)   # date → Timestamp (нужно для mdates)

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(daily_dt, daily.values, marker="o", lw=1.5, color="steelblue")
ax.set_title("Суточное энергопотребление дома, кВт·ч")
ax.set_xlabel("Дата")
ax.set_ylabel("кВт·ч")
ax.grid(alpha=0.3)

# подпись каждые 10 дней, формат "16.12"
ax.xaxis.set_major_locator(mdates.DayLocator(interval=10))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
fig.autofmt_xdate()

plt.tight_layout()
plt.savefig("output/daily_energy.png", dpi=150)
plt.close(fig)


# ---------- 10. ГРАФИК 2: минутный профиль мощности ----------
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(df["datetime"], df["Global_active_power"], lw=0.8, color="steelblue")
ax.set_title("Мощность дома, минутные замеры")
ax.set_xlabel("Время")
ax.set_ylabel("кВт")
ax.grid(alpha=0.3)
fig.autofmt_xdate()

plt.tight_layout()
plt.savefig("output/power_profile.png", dpi=150)
plt.close(fig)


# ---------- 11. ГРАФИК 3: средняя мощность по часам суток — ЛИНИЯ ----------
hourly = df.groupby(df["datetime"].dt.hour)["Global_active_power"].mean()

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(hourly.index, hourly.values, marker="o", lw=1.5, color="steelblue")
ax.set_xticks(range(0, 24))
ax.set_title("Средняя мощность по часам суток, кВт")
ax.set_xlabel("Час")
ax.set_ylabel("кВт")
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig("output/hourly_profile.png", dpi=150)
plt.close(fig)


# ---------- 12. ГРАФИК 4: сглаженный профиль мощности ----------
power = df["Global_active_power"].values
smooth = savgol_filter(power, window_length=61, polyorder=3)

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(df["datetime"], power, alpha=0.3, label="сырые")
ax.plot(df["datetime"], smooth, color="red", label="сглаженные")
ax.set_title("Мощность: сырые данные и сглаживание (Savitzky–Golay)")
ax.set_xlabel("Время")
ax.set_ylabel("кВт")
ax.legend()
ax.grid(alpha=0.3)
fig.autofmt_xdate()

plt.tight_layout()
plt.savefig("output/power_smoothed.png", dpi=150)
plt.close(fig)


# ---------- 13. Итог ----------
print("Готово. Файлы в", os.path.abspath("output"))
print(" - daily_energy.png")
print(" - power_profile.png")
print(" - hourly_profile.png")
print(" - power_smoothed.png")
print(" - daily_energy.xlsx")