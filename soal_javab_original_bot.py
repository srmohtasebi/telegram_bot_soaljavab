from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import InputMediaPhoto

# توکن بات تلگرام خود را اینجا وارد کنید
TOKEN = "7466425138:AAHYy-jD2LXvqLfWCO-0OMNDQWe2KFi3zwE"

# اتصال به گوگل شیت
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)  # مسیر فایل JSON را تنظیم کنید
client = gspread.authorize(creds)
sheet = client.open("StudentsCredits").sheet1  # نام شیت شما

# لیست معلم‌های ریاضی و فیزیک
math_teachers = ['6793258867', '6337921786']
physics_teachers = ['486322999', '486322999']

# پیام خوش‌آمدگویی برای کاربران جدید
WELCOME_MESSAGE = """
سلام دوست عزیز
"سوال-جواب"
رو چندتا از معلم‌های سمپاد راه انداختن تا هیچوقت تو هیچ سوالی گیر نکنی😍😎
اینجا جاییه که می‌تونی سوالات خودت در زمینه ریاضی و فیزیک، به معلم‌های خبره بفرستی و به سرعت پاسخ بگیری. ✨

🔹 چی کار می‌تونی بکنی؟
هر وقت ایرادی یا سوالی داشتی می‌تونی سریع به یکی از اساتید ما وصل بشی و سریع رفع اشکل کنی. کافیه روی درس مد نظرت کلیک کنی و سوالت رو بپرسی.🎓

📌 راستی!
اولین اعتبار رو "سوال-جواب"  به افتخار آشنایی باهات هدیه میده پس اولین سوالت رو رایگان بپرس🌻😉

ارتباط با ادمین @soaljavab_admin
⚠️اگه تنظیمات حریم خصوصی رو جوری تنظیم کردی که فقط مخاطبین بتونن بهت پیام بدن، تغییرش بده تا استاد بتونه بهت وصل شه⚠️
"""

# پیام خوش‌آمدگویی برای کاربران جدید
WELCOME_MESSAGE_NOT_USERNAME = """
سلام دوست عزیز
"سوال-جواب"
رو چندتا از معلم‌های سمپاد راه انداختن تا هیچوقت تو هیچ سوالی گیر نکنی😍😎
اینجا جاییه که می‌تونی سوالات خودت در زمینه ریاضی و فیزیک، به معلم‌های خبره بفرستی و به سرعت پاسخ بگیری. ✨

🔹 چی کار می‌تونی بکنی؟
هر وقت ایرادی یا سوالی داشتی می‌تونی سریع به یکی از اساتید ما وصل بشی و سریع رفع اشکل کنی. کافیه روی درس مد نظرت کلیک کنی و سوالت رو بپرسی.🎓

📌 راستی!
اولین اعتبار رو "سوال-جواب" به افتخار آشنایی باهات هدیه میده پس اولین سوالت رو رایگان بپرس🌻😉

ارتباط با ادمین @soaljavab_admin

⚠️ شما نام کاربری (username)تلگرام نداری و استاد نمی‌تونه مستقیم بهت پیام بده، حتما نام کاربری انتخاب کن ⚠️
"""


# اعتبار اولیه برای هر دانش‌آموز
INITIAL_CREDIT = 1

# دریافت اعتبار کاربر از گوگل شیت
def get_credit(chat_id):
    records = sheet.get_all_records()
    for row in records:
        if row['chat_id'] == chat_id:
            return row['credit']
    return None

def add_student_if_new(chat_id, username):
    if get_credit(chat_id) is None:
        # اضافه کردن کاربر جدید با chat_id و اعتبار اولیه
        row_data = [chat_id, username, INITIAL_CREDIT, '', '', '', 'telegram']
        sheet.append_row(row_data, table_range="A:G")
    elif username != "NoUsername":
        # اگر کاربر از قبل ثبت شده ولی نام کاربری به‌روزرسانی نشده است
        cell = sheet.find(str(chat_id))
        username_cell = sheet.cell(cell.row, 2)  # ستون B: username
        if username_cell.value == "NoUsername":
            sheet.update_cell(cell.row, 2, username)  # به‌روزرسانی username




# کاهش اعتبار کاربر
def decrement_credit(chat_id):
    cell = sheet.find(str(chat_id))
    credit_cell = sheet.cell(cell.row, cell.col + 2)
    current_credit = int(credit_cell.value)
    sheet.update_cell(cell.row, cell.col + 2, current_credit - 1)

# تابع افزایش اعتبار دعوت‌کننده
async def update_inviter_credit(inviter_chat_id):
    cell = sheet.find(str(inviter_chat_id))
    if cell:
        credit_cell = sheet.cell(cell.row, cell.col + 2)
        current_credit = int(credit_cell.value)
        sheet.update_cell(cell.row, cell.col + 2, current_credit + 1)

# تابع شروع بات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    user = update.message.from_user
    username = user.username if user.username else "NoUsername"
    
    # بررسی پارامتر لینک دعوت
    args = context.args
    if args:
        inviter_chat_id = args[0]  # شناسه کاربر دعوت‌کننده
        if inviter_chat_id.isdigit():
            inviter_chat_id = int(inviter_chat_id)

            # بررسی اینکه کاربر جدید است یا خیر
            is_new_user = get_credit(chat_id) is None
            if is_new_user:
                await update_inviter_credit(inviter_chat_id)  # افزایش اعتبار دعوت‌کننده
                # اطلاع به کاربر دعوت‌کننده
                await context.bot.send_message(
                    chat_id=inviter_chat_id,
                    text="یک کاربر از طریق دعوت شما به ربات پیوست و اعتبار شما افزایش یافت! 🎉"
                )
            else:
                # پیام به کاربری که قبلاً ثبت‌نام کرده است
                await update.message.reply_text("شما قبلاً در بات ثبت‌نام کرده‌اید.")

    add_student_if_new(chat_id, username)

    # پیام خوش‌آمدگویی به کاربر
    if user.username:
        await update.message.reply_text(WELCOME_MESSAGE)
    else:
        # ارسال پیام به کاربر با دکمه‌های اینلاین برای تنظیم نام کاربری
        keyboard = [
            [InlineKeyboardButton("آموزش ثبت نام کاربری", callback_data="guide_username")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(WELCOME_MESSAGE_NOT_USERNAME, reply_markup=reply_markup)


    # نمایش دکمه‌ها
    reply_keyboard = [
        ['سوال ریاضی دارم', 'سوال فیزیک دارم'],
        ['معرفی به دیگران', 'راهنما و قوانین'],
        ['خرید اعتبار', 'رزومه دبیران'],
        ['ناحیه کاربری'],
        ['تکمیل اطلاعات من(اختیاری)'],
        ['درباره ما']
    ]
    await update.message.reply_text(
        "گزینه مد نظرت رو انتخاب کن",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )



# پیام دعوت دیگران
async def invite_others(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    invite_link = f"https://t.me/soal_javab_original_bot?start={chat_id}"
    invite_message = (
        "دوست عزیز! 🎉\n"
        "برای دریافت اعتبار بیشتر، دوستات رو به این ربات دعوت کن. "
        "با هر دوستی که از طریق لینک شما به ربات بپیوندد، یک واحد اعتبار به حساب شما اضافه میشه. 😊\n\n"
        "لینک دعوت اختصاصی شما: \n"
        f"{invite_link}\n\n"
        "این لینک را با دوستان خود به اشتراک بگذارید و از پاداش‌های ما بهره‌مند شوید! 🎁"
    )
    await update.message.reply_text(invite_message)



# تابع برای هندل کردن کلیک بر روی دکمه راهنمای ست کردن نام کاربری
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "guide_username":
        # مسیر تصاویر
        image_paths = ["1.png", "2.png", "3.png", "4.png"]

        # ساخت لیست تصاویر برای ارسال به صورت آلبوم
        media_group = []
        for image_path in image_paths:
            with open(image_path, "rb") as image:
                media_group.append(InputMediaPhoto(image.read()))

        # ارسال تصاویر به صورت آلبوم
        await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)



# تابع برای نمایش رزومه دبیران
async def show_teachers_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("مرتضی استاد عظیم", callback_data="resume_morteza"),
         InlineKeyboardButton("سیدرضا محتسبی", callback_data="resume_sayedreza")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    resume_message = """
برای دیدن رزومه روی نام دبیر کلیک کن.
"""
    await update.message.reply_text(resume_message, reply_markup=reply_markup)

# تابع برای هندل کردن کلیک روی دکمه‌های رزومه
async def resume_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "resume_morteza":
        # ارسال عکس و متن رزومه مرتضی استاد عظیم
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=open("ostadazim.jpg", "rb"),  # فایل عکس مرتضی استاد عظیم
            caption="""
- 7 سال سابقه تدریس در مدارس سمپاد (حلی1،حلی3،)
- سر گروه فیزیک حلی3
"""
        )
    elif query.data == "resume_sayedreza":
        # ارسال عکس و متن رزومه سیدرضا محتسبی
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=open("mohtasebi.jpg", "rb"),  # فایل عکس سیدرضا محتسبی
            caption="""
- 10 سال سابقه تدریس در مدارس سمپاد (حلی1،حلی2،حلی3،شهید بهشتی شهر ری)
- معاون آموزش سابق حلی3
- تدریس در مدارس علوی، پیام امام، پیروان
- تدریس تیزهوشان در موسسه اف ریاضی
- داور جشنواره خوارزمی
"""
            
        )
    

# مدیریت پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    user = update.message.from_user  # تعریف متغیر user
    username = user.username if user.username else "NoUsername"
    user_message = update.message.text.lower()
    credit = get_credit(chat_id)
    form_step = context.user_data.get("form_step", None)

    # بررسی و به‌روزرسانی نام کاربری
    if username != "NoUsername":
        try:
            cell = sheet.find(str(chat_id))  # پیدا کردن کاربر در شیت
            username_cell = sheet.cell(cell.row, 2)  # ستون B: username
            if username_cell.value != username:  # اگر نام کاربری تغییر کرده باشد
                sheet.update_cell(cell.row, 2, username)  # به‌روزرسانی نام کاربری در شیت
                await update.message.reply_text("نام کاربری شما با موفقیت به‌روزرسانی شد! 🎉")
        except gspread.CellNotFound:
            # اگر کاربر در شیت وجود ندارد، پیام خطا نمایش داده شود
            await update.message.reply_text("کاربری با این شناسه یافت نشد. لطفاً ابتدا با دستور /start ثبت‌نام کنید.")
    else:
        # اگر کاربر نام کاربری نداشت، به او اطلاع دهید
        await update.message.reply_text(
            "شما هنوز نام کاربری انتخاب نکرده‌اید. لطفاً یک نام کاربری در تنظیمات تلگرام خود انتخاب کنید."
        )

    # مدیریت فرم اطلاعات شخصی
    if user_message == "تکمیل اطلاعات من(اختیاری)":
        # آغاز فرم
        await update.message.reply_text("کدوم پایه تحصیلی هستی:")
        context.user_data["form_step"] = "grade"
        context.user_data["user_data"] = {"chat_id": chat_id}

    elif form_step == "grade":
        context.user_data["user_data"]["grade"] = user_message
        await update.message.reply_text("از کدوم شهری:")
        context.user_data["form_step"] = "city"

    elif form_step == "city":
        context.user_data["user_data"]["city"] = user_message
        await update.message.reply_text("شماره موبایلت رو وارد میکنی:")
        context.user_data["form_step"] = "phone_number"

    elif form_step == "phone_number":
        context.user_data["user_data"]["phone_number"] = user_message
        await update.message.reply_text("فرم شما تکمیل شد! در حال ذخیره اطلاعات...")
        # ذخیره اطلاعات در گوگل شیت (فقط اطلاعات تکمیلی)
        user_data = context.user_data["user_data"]
        try:
              # جستجوی کاربر با استفاده از chat_id
            cell = sheet.find(str(user_data["chat_id"]))
    
            # به‌روزرسانی اطلاعات تکمیلی در شیت، در ستون‌های مربوط به هر اطلاعات
            
            sheet.update_cell(cell.row, cell.col + 3, user_data["grade"])          # grade
            sheet.update_cell(cell.row, cell.col + 4, user_data["city"])           # city
            sheet.update_cell(cell.row, cell.col + 5, user_data["phone_number"])  # phone_number

            await update.message.reply_text("اطلاعات شما با موفقیت به‌روزرسانی شد! 🎉")
            # ریست کردن مرحله فرم
            context.user_data["form_step"] = None
        except gspread.CellNotFound:
            await update.message.reply_text("کاربری با این شناسه یافت نشد. ابتدا باید ثبت‌نام کنید.")

    elif user_message == 'راهنما و قوانین':
        await update.message.reply_text("""راهنمایی

🔻چطوری سوال بپرسم؟
- کافیه روی درسی که سوال داری بزنی.
بعدش سوالت رو بنویس و منتظر پیام استاد باش.


🔻چطوری به استاد وصل بشم؟
-ما سوالت رو برای اساتید میفرستیم. اولین استادی که سوالت رو تایید کرد بهت پیام میده. پس منتظر پیام استاد باش.

⚠️ اگه اکانتت رو برای ارسال پیام بستی باز کن که استاد بتونه بهت پیام بده

🔻پایان چت با استاد چه زمانیه؟
-پایان چت توافقی هستش و برای ما مهمه اشکال شما بر طرف شده باشه.

🔻سوالم فرمول داره سخته برام توی بات بنویسم!
-کافیه موضوع سوالت رو بنویسی تا استاد از کلیتش با خبر بشه. بعدش که به استاد وصل شدی از فرمول ها عکس بگیر.

🔻هزینه هر اتصال چقدره؟
-حق الزحمه استاد برای هر صبحت با شما 100هزار تومان هستش.

🔻چطوری اعتبارم رو شارژ کنم؟
-کافیه روی دکمه خرید اعتبار بزنی و از طریق لینک درگاه بانکی پرداخت انجام بدی.

راستی!
اولین اعتبار رو "سوال-جواب" به افتخار آشنایی باهات هدیه میده🌻😉

سوال دیگه‌ای داشتی به ادمین پیام بده👇
@soaljavab_admin""")
    elif user_message == 'خرید اعتبار':
        await update.message.reply_text(
        """🔻برای خرید اعتبار کافیه عدد مد نظرت رو در درگاه بانکی زیر پرداخت کنی 👇
https://www.payping.ir/d/sHkT
⚠️طبق قوانین بانکی برای پرداخت باید فیلتر شکن خاموش باشه
⚠️ حتما رسیدش رو برای ادمین بفرست که به اعتبارت اضافه کنیم.
ارتباط با ادمین @soaljavab_admin

🔻هزینه هر اتصال به استاد 100 هزار تومن هستش پس اگر مثلا 300 هزارتون شارژ کنی 3 اعتبار بهت اضافه میشه

اگه اشکال فوری داشتی و اون لحظه پول نداشتی به ادمین پیام بزن کارت رو راه میندازه😉""")

    
    elif user_message == 'درباره ما':
        await update.message.reply_text("""خیلی وقت‌ها پیش میاد که به یه مشکلی برخورد میکنی، مثلا سریع باید رفع اشکال کنی یا شب امتحان نیاز داری یه موضوعی برات بهتر توضیح داده بشه.🎯
از طرفی وقت معلم خصوصی گرفتن نداری و یا به خاطر یه سوال هزینه کردن واسه معلم خصوصی نمی‌صرفه💯
اینجاست که نیاز داری سریع به یه استاد خبره وصل بشی👌

"سوال جواب"
رو چندتا از معلم‌های سمپاد راه انداختن تا نذارن تو هیچ مساله‌ای بمونی
یعنی سریع رفع اشکال کنی✍
سطحت رو ببری بالا💪
و هیچوقت گیر نکنی ⬆🔥

📍آدرس ما:
تهران، خیابان سنایی، جواد زاده هشتم غربی پلاک 3 - خانه نوآوری هنروما
📱بات بله:
https://ble.ir/soal_javab_bot                                      
📲ارتباط با ما:
@soaljavab_admin""")

    elif user_message == 'ناحیه کاربری':
    # واکشی اطلاعات کاربر از شیت با استفاده از chat_id
        try:
            cell = sheet.find(str(chat_id))
            row_data = sheet.row_values(cell.row)

             # نمایش اطلاعات کاربر
            username = row_data[1] if len(row_data) > 1 else "نام کاربری موجود نیست"
            credit = row_data[2] if len(row_data) > 2 else "نامشخص"
            grade = row_data[3] if len(row_data) > 3 else "نامشخص"
            city = row_data[4] if len(row_data) > 4 else "نامشخص"
            phone_number = row_data[5] if len(row_data) > 5 else "نامشخص"

            await update.message.reply_text(
                f"کد عضویت شما = {chat_id}\nنام کاربری = {username}\nاعتبار باقی‌مانده = {credit}\nپایه تحصیلی = {grade}\nشهر = {city}\nشماره تماس = {phone_number}"
            )
        except Exception as e:
            await update.message.reply_text("کاربری با این شناسه یافت نشد.")

    elif user_message == 'رزومه دبیران':
        await show_teachers_resume(update, context)

    elif user_message == 'معرفی به دیگران':
        await invite_others(update, context)

    elif credit is None or credit <= 0:
        await update.message.reply_text("شما اعتبار کافی برای پرسیدن سوال ندارید. لطفاً ابتدا اعتبار خود را شارژ کنید.")
        return
    elif user_message == 'سوال ریاضی دارم':
        await update.message.reply_text(" سوال ریاضی خودت رو بنویس.")
        context.user_data['subject'] = 'math'
    elif user_message == 'سوال فیزیک دارم':
        await update.message.reply_text(" سوال فیزیک خودت رو بنویس.")
        context.user_data['subject'] = 'physics'
    
    else:
        if 'subject' in context.user_data:
            subject = context.user_data['subject']
            teacher = random.choice(math_teachers if subject == 'math' else physics_teachers)

            # کاهش اعتبار قبل از ارسال سوال
            decrement_credit(chat_id)
            await update.message.reply_text(f"اعتبار باقی‌مانده شما: {credit - 1}")
            await update.message.reply_text("سوال به اساتید ارسال شد. در اولین فرصت استاد تو شخصی بهت پیام میده")

            # دکمه‌های تایید و رد کردن برای معلم
            keyboard = [
                [
                    InlineKeyboardButton("تایید و چت با دانش آموز", callback_data=f"accept_{update.effective_user.username}"),
                    InlineKeyboardButton("رد کردن", callback_data="reject")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(
                    chat_id=teacher,
                    text=f"سوال از {update.effective_user.username}:\n{update.message.text}",
                    reply_markup=reply_markup
                )
            except Exception as e:
                await update.message.reply_text("متاسفانه مشکلی در ارسال سوال به معلم پیش آمده است.")
                print(f"Error sending message to teacher {teacher}: {e}")
        else:
            await update.message.reply_text("لطفا ابتدا مشخص کنید سوال ریاضی دارید یا فیزیک.")



# مدیریت کلیک روی دکمه‌های تایید و رد کردن
async def approval_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data.startswith("accept_"):
        student_username = query.data.split("_")[1]
        if student_username:
            await query.edit_message_text(
                f"شما با دانش‌آموز به نام @{student_username} در ارتباط هستید. "
                f"برای شروع چت به صفحه او بروید: [چت با @{student_username}](https://t.me/{student_username})",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("نام کاربری دانش‌آموز موجود نیست.")
    elif query.data == "reject":
        await query.edit_message_text("شما درخواست دانش‌آموز را رد کردید.")

        # شناسه منحصربه‌فرد برای سوال دانش‌آموز (ترکیب student_username و subject)
        student_username = query.message.text.split("\n")[0].split(" ")[-1]
        subject = context.user_data.get('subject')
        question_id = f"{student_username}_{subject}"

        # اطمینان از ایجاد `rejected_teachers` در `context.application` برای پیگیری ردکنندگان
        if not hasattr(context.application, 'rejected_teachers'):
            context.application.rejected_teachers = {}

        # اگر لیست معلمان ردکننده برای این سوال خاص وجود ندارد، ایجاد کنید
        if question_id not in context.application.rejected_teachers:
            context.application.rejected_teachers[question_id] = set()

        # اضافه کردن معلم فعلی به لیست ردکنندگان
        current_teacher = int(query.message.chat_id)
        context.application.rejected_teachers[question_id].add(current_teacher)

        question_text = query.message.text.split(":\n")[1]

        # ایجاد لیست معلمان موجود به جز معلمان ردکننده
        available_teachers = math_teachers if subject == 'math' else physics_teachers
        available_teachers = [int(t) for t in available_teachers if int(t) not in context.application.rejected_teachers[question_id]]

        # ارسال سوال به معلم جدید یا نمایش پیام خطا
        if available_teachers:
            new_teacher = random.choice(available_teachers)

            # دکمه‌های تایید و رد کردن برای معلم جدید
            keyboard = [
                [
                    InlineKeyboardButton("تایید و چت با دانش آموز", callback_data=f"accept_{student_username}"),
                    InlineKeyboardButton("رد کردن", callback_data="reject")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                await context.bot.send_message(
                    chat_id=new_teacher,
                    text=f"سوال از {student_username}:\n{question_text}",
                    reply_markup=reply_markup
                )
            except Exception as e:
                await query.message.reply_text(f"متاسفانه مشکلی در ارسال سوال به معلم جدید پیش آمده است: {e}")
                print(f"Error sending message to new teacher {new_teacher}: {e}")
        else:
            # بازگرداندن اعتبار دانش‌آموز اگر هیچ معلمی درخواست را قبول نکرد
            chat_id = query.message.chat_id  # شناسه دانش‌آموز
            cell = sheet.find(str(chat_id))
            credit_cell = sheet.cell(cell.row, cell.col + 2)
            current_credit = int(credit_cell.value)
            sheet.update_cell(cell.row, cell.col + 2, current_credit + 1)
            await query.message.reply_text("متاسفانه هیچ معلمی درخواست شما را قبول نکرد. اعتبار شما بازگردانده شد.")

# راه‌اندازی بات
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(resume_button_handler, pattern="^resume_"))
    application.add_handler(CallbackQueryHandler(approval_button_handler, pattern="^(accept_|reject)"))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.run_polling()

if __name__ == "__main__":
    main()
