# CampusConnect

CampusConnect lists 30 student services at the University of Texas at Arlington. You can look up
an office by name or describe what you need. For example, “I lost my student ID” points you to
the Mav Card Office.

## Run it locally

**Windows 10 or 11 (64-bit Intel or AMD):** Right-click the ZIP and choose **Extract All**. Open
the `Source_Code` folder and double-click `Start-CampusConnect.cmd`. Python is
included.

**macOS or Linux:** With Python 3.11 or later installed, open a terminal in the extracted
`CampusConnect` folder and run:

```sh
python3 src/start.py
```

If no browser tab opens, copy the full address printed in the terminal into your browser. Keep
the terminal open while you use the site; press Ctrl+C there to stop it. CampusConnect runs on
your computer and typed search works offline. Only external links need internet access.

## Using the site

You can browse the directory, use **Find help** and read notices without signing in. The
directory opens with nine listings. **Load more** adds up to nine at a time. Search and filters
check every published listing, including ones you haven't loaded.

**Students:** Choose **Sign in**, then **Create a student account** to save bookmarks and see
recently viewed offices. Use a new password for CampusConnect. No UTA account is required.

**Administrators:** Double-click `Create-Admin.cmd` on Windows. On macOS or Linux, run this from
the `CampusConnect` folder:

```sh
python3 src/manage.py create-admin
```

The password prompt stays blank as you type. Enter at least 12 characters and confirm when
asked. Then sign in on the site to edit listings, publish notices or see usage totals for the
last 7 or 30 days.

## Find help feedback and voice search

After a search, choose **Yes** or **No** under **Did this solve your problem?**.
A No response can include an optional reason. Questions with no confident match are
saved automatically. Administrators can open **Unanswered questions** to view these
searches and student reports, then mark entries reviewed or reopen them. Leave names,
student IDs, and other personal details out of your question.

In a supported browser, choose **Speak your question**, allow microphone access, and
review or edit the transcript before choosing **Find resources**. Voice uses the browser's
speech recognition and may need internet access or send audio to the browser provider.
CampusConnect receives the question text on submission. You can always type a question.

## Project notes

The React interface is in `src/frontend/` and `src/components/`; the Python server is in
`src/backend/`. The first launch loads the offices from `src/data-source/catalog.json`. Accounts
and edits are saved in a local SQLite database under `src/instance/`.

## AI in the project

We used **Figma Make** for the original interface prototype.

The directory search and **Find help** use MinishLab’s pretrained **Model2Vec** model,
[`potion-base-8M`](https://huggingface.co/minishlab/potion-base-8M). It runs on the local
Python server. It represents the words in a question and each office’s services as vectors
and compares them by cosine similarity. Office names, campus keywords and a few enrollment
rules contribute to the final order. New listings use their published text; archived offices
never appear. The guide asks for clarification when close matches point to different offices.

For example, a student wanting to drop a class and take it later sees Academic Advising, with
a link to the Registrar’s [add/drop procedures](https://www.uta.edu/administration/registrar/students/registration/courses/add-drop-withdrawal).
A question about what dropping the class would do to a grant points to Financial Aid.

**Draft a question** uses a separate, small next-word model running in the browser with
**TensorFlow.js**. The draft follows the selected office and service. Students can edit and
copy it; the site doesn’t send it to anyone. Contact details come from the directory.
The ZIP includes both models. You don’t need an AI account, API key or first-run download.

## Tests and development

Run the tests from the `Source_Code` folder. They use a temporary database, so your
local accounts and listings are untouched.

**Windows PowerShell:**

```powershell
.\runtime\windows-x64\python.exe -X utf8 -m unittest discover -s src\tests -v
```

**macOS or Linux:**

```sh
python3 -m unittest discover -s src/tests -v
```

The browser files are already built. If you change the interface, rebuild it with Node.js 24 and
npm:

```sh
cd src
npm ci
npm run typecheck
npm run build
```

The original search weights and tokenizer are in `src/ai/potion-base-8M/`. They are used
as published; the source revision and license are in `src/THIRD-PARTY-NOTICES.txt`.
The campus service descriptions used for ranking are in `src/ai/service-intents.json`.
The tests report first-office matches on two small sets of student questions.
To retrain the optional draft model only, run `python3 ai/train-browser.py` from `src/`
with NumPy installed, then rebuild the interface.
