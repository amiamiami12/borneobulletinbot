import discord
from discord.ext import commands
from selenium import webdriver
from datetime import datetime, timedelta
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import pytz

import os
from dotenv import load_dotenv
load_dotenv


brunei_timezone = pytz.timezone('Asia/Brunei')

def time_since_posted(post_time):
    current_time = datetime.now(brunei_timezone)
    post_time = post_time.replace(tzinfo=brunei_timezone)
    time_diff = current_time - post_time
    return time_diff

service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)

driver.get("https://borneobulletin.com.bn/category/national/#")

time.sleep(5)

PREFIX = "!"

intents = discord.Intents.default()
intents.members = True  # Required to receive member events
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'Pong! Latency: {latency}ms')

def get_article_image_thumbnail_url(article):
    try:
        image_element = article.find_element(By.CSS_SELECTOR, "img.size-full")
        image_url = image_element.get_attribute("src")
        return image_url
    except:
        return ""

def scrape_news():
    scraped_data = []
    articles = driver.find_element(By.ID, "tdi_55")
    articlebox = articles.find_elements(By.CLASS_NAME, "td-module-meta-info")

    for article in articlebox:
        try:
            title = article.find_element(By.XPATH, ".//h3").text
            print(title)
            post_time_element = article.find_element(By.XPATH, ".//time").get_attribute("datetime")
            post_time_str = post_time_element
            post_time = datetime.strptime(post_time_str, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=brunei_timezone)

            article_element = article.find_element(By.CLASS_NAME, "entry-title")
            article_url = article_element.find_element(By.TAG_NAME, "a").get_attribute("href")

            print(article_url)
            print(get_article_image_thumbnail_url)

            if time_since_posted(post_time) < timedelta(days=1):
                time_since_posted_str = str(time_since_posted(post_time))
                days_diff = time_since_posted(post_time).days
                hours_diff = time_since_posted(post_time).seconds // 3600
                minutes_diff = (time_since_posted(post_time).seconds // 60) % 60
                time_since_posted_str = f"{days_diff} days, {hours_diff} hours, {minutes_diff} minutes ago"

                scraped_data.append([title, post_time, time_since_posted_str, article_url])

        except Exception as e:
            print(f"Error scraping article: {e}")

    return scraped_data

def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Title', 'Date', 'Time Since Posted', 'Link URL'])
        writer.writerows(data)

@bot.command()
async def news(ctx):
    scraped_data = scrape_news()
    for data in scraped_data:
        embed = discord.Embed(title="Latest News Articles", color=0xFF69B4)  # Pink color
        embed.add_field(name="Title", value=data[0], inline=False)
        embed.add_field(name="Date", value=data[1], inline=False)
        embed.add_field(name="Time Since Posted", value=data[2], inline=False)
        embed.add_field(name="URL to Article", value=data[3], inline=False)
        image_url = get_article_image_thumbnail_url(data)
        if image_url != "No image available":
            embed.set_image(url=image_url)
        await ctx.send(embed=embed)

bot.run(os.getenv("DISCORD_API_KEY"))

