@echo off
echo Installing dependencies...
pip install -r requirements.txt
npm install

echo Building React app...
npm run build

echo Starting application...
python app.py