from flask import Flask, render_template_string, request, jsonify, redirect
import os
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

app = Flask(__name__)

STORAGE_ACCOUNT_NAME = os.getenv('STORAGE_ACCOUNT_NAME')
CONTAINER_NAME = os.getenv('CONTAINER_NAME')
STORAGE_CONNECTION_STRING = os.getenv('STORAGE_CONNECTION_STRING')
STORAGE_ACCOUNT_KEY = os.getenv('STORAGE_ACCOUNT_KEY')

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AzureVault — Secure File Manager</title>
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --bg: #0a0a0f;
            --surface: #111118;
            --surface2: #18181f;
            --border: rgba(255,255,255,0.07);
            --border-bright: rgba(255,255,255,0.15);
            --accent: #6c63ff;
            --accent2: #ff6584;
            --accent3: #43e97b;
            --text: #e8e8f0;
            --muted: #6b6b80;
            --danger: #ff4d6d;
            --font-head: 'Syne', sans-serif;
            --font-mono: 'DM Mono', monospace;
            --radius: 12px;
            --shadow: 0 8px 32px rgba(0,0,0,0.5);
        }

        body {
            background: var(--bg);
            color: var(--text);
            font-family: var(--font-mono);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* Noise texture overlay */
        body::before {
            content: '';
            position: fixed;
            inset: 0;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
            pointer-events: none;
            z-index: 0;
            opacity: 0.4;
        }

        /* Glowing orbs */
        .orb {
            position: fixed;
            border-radius: 50%;
            filter: blur(100px);
            pointer-events: none;
            z-index: 0;
        }
        .orb-1 { width: 400px; height: 400px; background: rgba(108,99,255,0.12); top: -100px; right: -100px; }
        .orb-2 { width: 300px; height: 300px; background: rgba(255,101,132,0.08); bottom: 200px; left: -50px; }
        .orb-3 { width: 200px; height: 200px; background: rgba(67,233,123,0.06); top: 50%; left: 50%; }

        /* ---- LAYOUT ---- */
        .shell {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 260px 1fr;
            min-height: 100vh;
        }

        /* ---- SIDEBAR ---- */
        .sidebar {
            background: var(--surface);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 0;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
        }

        .logo {
            padding: 28px 24px 20px;
            border-bottom: 1px solid var(--border);
        }

        .logo-wordmark {
            font-family: var(--font-head);
            font-size: 1.4rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            background: linear-gradient(135deg, #6c63ff, #ff6584);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-sub {
            font-size: 0.7rem;
            color: var(--muted);
            margin-top: 2px;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }

        .nav-section {
            padding: 20px 16px 10px;
        }

        .nav-label {
            font-size: 0.65rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            color: var(--muted);
            padding: 0 8px;
            margin-bottom: 8px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.85rem;
            color: var(--muted);
            border: 1px solid transparent;
            text-decoration: none;
        }

        .nav-item:hover, .nav-item.active {
            background: var(--surface2);
            color: var(--text);
            border-color: var(--border);
        }

        .nav-item.active {
            color: var(--accent);
            border-color: rgba(108,99,255,0.3);
            background: rgba(108,99,255,0.08);
        }

        .nav-item i { font-size: 1rem; }

        .sidebar-stats {
            margin-top: auto;
            padding: 16px;
            border-top: 1px solid var(--border);
        }

        .stat-pill {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: var(--surface2);
            border-radius: 8px;
            font-size: 0.75rem;
            margin-bottom: 6px;
        }

        .stat-pill-label { color: var(--muted); }
        .stat-pill-value { color: var(--text); font-weight: 500; }

        /* ---- MAIN ---- */
        .main {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }

        .topbar {
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 16px 28px;
            display: flex;
            align-items: center;
            gap: 16px;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .page-title {
            font-family: var(--font-head);
            font-size: 1.1rem;
            font-weight: 700;
            flex: 1;
        }

        .search-wrap {
            flex: 1;
            max-width: 380px;
            position: relative;
        }

        .search-wrap i {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--muted);
            font-size: 0.9rem;
        }

        .search-input {
            width: 100%;
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text);
            font-family: var(--font-mono);
            font-size: 0.82rem;
            padding: 9px 12px 9px 34px;
            transition: border-color 0.2s;
            outline: none;
        }

        .search-input::placeholder { color: var(--muted); }
        .search-input:focus { border-color: var(--accent); }

        .filter-btns {
            display: flex;
            gap: 6px;
        }

        .filter-btn {
            padding: 7px 13px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-family: var(--font-mono);
            border: 1px solid var(--border);
            background: transparent;
            color: var(--muted);
            cursor: pointer;
            transition: all 0.2s;
        }

        .filter-btn:hover { border-color: var(--border-bright); color: var(--text); }
        .filter-btn.active { background: rgba(108,99,255,0.15); border-color: rgba(108,99,255,0.4); color: var(--accent); }

        .content {
            padding: 28px;
            flex: 1;
        }

        /* ---- TABS ---- */
        .tabs {
            display: flex;
            gap: 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 28px;
        }

        .tab {
            padding: 10px 20px;
            font-size: 0.82rem;
            cursor: pointer;
            color: var(--muted);
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            margin-bottom: -1px;
        }

        .tab:hover { color: var(--text); }
        .tab.active { color: var(--accent); border-bottom-color: var(--accent); }

        /* ---- STATS GRID ---- */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 28px;
        }

        .stat-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 20px;
            position: relative;
            overflow: hidden;
            transition: border-color 0.2s, transform 0.2s;
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
        }

        .stat-card:nth-child(1)::before { background: var(--accent); }
        .stat-card:nth-child(2)::before { background: var(--accent2); }
        .stat-card:nth-child(3)::before { background: var(--accent3); }
        .stat-card:nth-child(4)::before { background: #ffd166; }

        .stat-card:hover { border-color: var(--border-bright); transform: translateY(-2px); }

        .stat-num {
            font-family: var(--font-head);
            font-size: 2rem;
            font-weight: 800;
            line-height: 1;
            margin-bottom: 6px;
        }

        .stat-card:nth-child(1) .stat-num { color: var(--accent); }
        .stat-card:nth-child(2) .stat-num { color: var(--accent2); }
        .stat-card:nth-child(3) .stat-num { color: var(--accent3); }
        .stat-card:nth-child(4) .stat-num { color: #ffd166; }

        .stat-desc { font-size: 0.75rem; color: var(--muted); }
        .stat-icon { position: absolute; right: 16px; top: 16px; font-size: 1.4rem; opacity: 0.2; }

        /* ---- UPLOAD ZONE ---- */
        .upload-zone {
            border: 2px dashed var(--border);
            border-radius: var(--radius);
            padding: 48px 24px;
            text-align: center;
            background: var(--surface);
            transition: all 0.3s;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }

        .upload-zone.dragover {
            border-color: var(--accent);
            background: rgba(108,99,255,0.06);
        }

        .upload-zone-icon {
            font-size: 2.5rem;
            color: var(--accent);
            margin-bottom: 12px;
            display: block;
        }

        .upload-zone h3 {
            font-family: var(--font-head);
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 6px;
        }

        .upload-zone p {
            font-size: 0.8rem;
            color: var(--muted);
        }

        /* ---- PROGRESS ---- */
        .progress-list {
            margin-top: 16px;
        }

        .progress-item {
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .progress-header {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            margin-bottom: 8px;
        }

        .progress-name { color: var(--text); }
        .progress-pct { color: var(--accent); }

        .progress-bar-bg {
            height: 4px;
            background: var(--border);
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent), var(--accent2));
            border-radius: 4px;
            transition: width 0.3s;
        }

        .progress-bar-fill.done { background: var(--accent3); }
        .progress-bar-fill.error { background: var(--danger); }

        /* ---- BTN ---- */
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 10px 18px;
            border-radius: 8px;
            font-family: var(--font-mono);
            font-size: 0.82rem;
            font-weight: 500;
            cursor: pointer;
            border: none;
            transition: all 0.2s;
            text-decoration: none;
        }

        .btn-primary {
            background: var(--accent);
            color: #fff;
        }
        .btn-primary:hover { background: #5752e0; transform: translateY(-1px); box-shadow: 0 4px 14px rgba(108,99,255,0.4); }

        .btn-ghost {
            background: transparent;
            color: var(--muted);
            border: 1px solid var(--border);
        }
        .btn-ghost:hover { border-color: var(--border-bright); color: var(--text); }

        .btn-danger-sm {
            background: rgba(255,77,109,0.1);
            color: var(--danger);
            border: 1px solid rgba(255,77,109,0.2);
            padding: 6px 11px;
            font-size: 0.75rem;
        }
        .btn-danger-sm:hover { background: rgba(255,77,109,0.2); }

        .btn-icon {
            background: var(--surface2);
            border: 1px solid var(--border);
            color: var(--muted);
            padding: 6px 10px;
            font-size: 0.8rem;
        }
        .btn-icon:hover { border-color: var(--border-bright); color: var(--text); }

        .btn-upload {
            width: 100%;
            justify-content: center;
            margin-top: 16px;
            padding: 12px;
        }

        /* ---- FILES TABLE ---- */
        .files-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .view-toggle {
            display: flex;
            gap: 4px;
        }

        .view-btn {
            padding: 6px 10px;
            border-radius: 6px;
            border: 1px solid var(--border);
            background: transparent;
            color: var(--muted);
            cursor: pointer;
            transition: all 0.2s;
        }
        .view-btn.active { background: var(--surface2); color: var(--text); border-color: var(--border-bright); }

        .file-table-wrap {
            overflow-x: auto;
        }

        .file-table {
            width: 100%;
            border-collapse: collapse;
        }

        .file-table th {
            font-size: 0.7rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--muted);
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }

        .file-table td {
            padding: 13px 14px;
            font-size: 0.82rem;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
        }

        .file-table tr:last-child td { border-bottom: none; }
        .file-table tr:hover td { background: var(--surface2); }

        .file-name-cell {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .file-type-icon {
            width: 32px;
            height: 32px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.9rem;
            flex-shrink: 0;
        }

        .icon-img { background: rgba(108,99,255,0.15); color: var(--accent); }
        .icon-pdf { background: rgba(255,77,109,0.15); color: var(--danger); }
        .icon-doc { background: rgba(67,233,123,0.15); color: var(--accent3); }
        .icon-vid { background: rgba(255,165,0,0.15); color: orange; }
        .icon-zip { background: rgba(255,209,102,0.15); color: #ffd166; }
        .icon-txt { background: rgba(107,107,128,0.2); color: var(--muted); }
        .icon-default { background: var(--surface2); color: var(--muted); }

        .file-name-text { font-weight: 500; color: var(--text); }
        .file-size-text { color: var(--muted); }
        .file-date-text { color: var(--muted); }

        .action-btns { display: flex; gap: 6px; }

        /* ---- GRID VIEW ---- */
        .file-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 14px;
        }

        .file-grid-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 16px;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
            overflow: hidden;
        }

        .file-grid-card:hover { border-color: var(--border-bright); transform: translateY(-2px); box-shadow: var(--shadow); }

        .file-grid-icon {
            width: 48px; height: 48px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            margin-bottom: 12px;
        }

        .file-grid-name {
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 4px;
        }

        .file-grid-meta { font-size: 0.7rem; color: var(--muted); }

        .file-grid-actions {
            position: absolute;
            top: 8px; right: 8px;
            display: flex;
            gap: 4px;
            opacity: 0;
            transition: opacity 0.2s;
        }

        .file-grid-card:hover .file-grid-actions { opacity: 1; }

        .mini-btn {
            width: 26px; height: 26px;
            border-radius: 6px;
            border: 1px solid var(--border);
            background: var(--surface2);
            color: var(--muted);
            font-size: 0.7rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        .mini-btn:hover { color: var(--text); border-color: var(--border-bright); }
        .mini-btn.danger:hover { color: var(--danger); border-color: rgba(255,77,109,0.3); }

        /* ---- PREVIEW MODAL ---- */
        .modal-backdrop {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(8px);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }

        .modal-backdrop.show { display: flex; }

        .modal {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            max-width: 800px;
            width: 100%;
            max-height: 90vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            animation: modalIn 0.25s ease;
        }

        @keyframes modalIn {
            from { opacity: 0; transform: scale(0.95) translateY(10px); }
            to { opacity: 1; transform: scale(1) translateY(0); }
        }

        .modal-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .modal-title {
            font-family: var(--font-head);
            font-weight: 700;
            flex: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .modal-body {
            padding: 24px;
            overflow-y: auto;
            flex: 1;
        }

        .preview-img {
            max-width: 100%;
            max-height: 60vh;
            border-radius: 8px;
            display: block;
            margin: 0 auto;
        }

        .preview-text {
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            font-size: 0.8rem;
            line-height: 1.7;
            white-space: pre-wrap;
            max-height: 60vh;
            overflow-y: auto;
            color: var(--text);
        }

        .preview-pdf {
            width: 100%;
            height: 60vh;
            border-radius: 8px;
            border: none;
        }

        .preview-unsupported {
            text-align: center;
            padding: 48px;
            color: var(--muted);
        }

        .preview-unsupported i { font-size: 3rem; margin-bottom: 16px; display: block; }

        .modal-footer {
            padding: 16px 24px;
            border-top: 1px solid var(--border);
            display: flex;
            gap: 10px;
        }

        /* ---- SHARE MODAL ---- */
        .share-link-box {
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
        }

        .share-link-url {
            flex: 1;
            font-size: 0.78rem;
            color: var(--muted);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .expiry-opts {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-bottom: 16px;
        }

        .expiry-opt {
            padding: 10px;
            text-align: center;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.78rem;
            cursor: pointer;
            color: var(--muted);
            transition: all 0.2s;
        }

        .expiry-opt:hover, .expiry-opt.sel {
            border-color: var(--accent);
            color: var(--accent);
            background: rgba(108,99,255,0.08);
        }

        /* ---- EMPTY ---- */
        .empty-state {
            text-align: center;
            padding: 80px 20px;
            color: var(--muted);
        }

        .empty-state i { font-size: 3rem; margin-bottom: 16px; display: block; opacity: 0.4; }
        .empty-state h3 { font-family: var(--font-head); font-size: 1.1rem; margin-bottom: 8px; color: var(--text); }
        .empty-state p { font-size: 0.82rem; }

        /* ---- TOAST ---- */
        .toast-wrap {
            position: fixed;
            bottom: 28px;
            right: 28px;
            z-index: 2000;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .toast {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px 18px;
            font-size: 0.8rem;
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 260px;
            animation: toastIn 0.3s ease;
            box-shadow: var(--shadow);
        }

        @keyframes toastIn {
            from { opacity: 0; transform: translateX(20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .toast.success { border-color: rgba(67,233,123,0.3); }
        .toast.success i { color: var(--accent3); }
        .toast.error { border-color: rgba(255,77,109,0.3); }
        .toast.error i { color: var(--danger); }
        .toast.info i { color: var(--accent); }

        /* ---- RESPONSIVE ---- */
        @media (max-width: 1024px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }

        @media (max-width: 768px) {
            .shell { grid-template-columns: 1fr; }

            .sidebar {
                position: fixed;
                left: 0; top: 0; bottom: 0;
                transform: translateX(-100%);
                z-index: 200;
                width: 260px;
                transition: transform 0.3s;
            }

            .sidebar.open { transform: translateX(0); }

            .sidebar-overlay {
                display: none;
                position: fixed;
                inset: 0;
                background: rgba(0,0,0,0.5);
                z-index: 199;
            }

            .sidebar-overlay.show { display: block; }

            .topbar { padding: 12px 16px; }
            .content { padding: 16px; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
            .filter-btns { display: none; }
            .page-title { display: none; }
            .search-wrap { max-width: 100%; }
            .menu-btn { display: flex !important; }

            .action-btns { flex-direction: column; }
        }

        @media (max-width: 480px) {
            .stats-grid { grid-template-columns: 1fr 1fr; }
            .file-table th:nth-child(3),
            .file-table td:nth-child(3),
            .file-table th:nth-child(4),
            .file-table td:nth-child(4) { display: none; }
        }

        .menu-btn {
            display: none;
            align-items: center;
            justify-content: center;
            width: 36px; height: 36px;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: transparent;
            color: var(--text);
            cursor: pointer;
            font-size: 1rem;
        }

        input[type="file"] { display: none; }

        .status-dot {
            width: 6px; height: 6px;
            border-radius: 50%;
            background: var(--accent3);
            display: inline-block;
            margin-right: 6px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
    </style>
</head>
<body>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>

<div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>

<div class="shell">
    <!-- SIDEBAR -->
    <aside class="sidebar" id="sidebar">
        <div class="logo">
            <div class="logo-wordmark"><i class="bi bi-lock-fill"></i> AzureVault</div>
            <div class="logo-sub"><span class="status-dot"></span>All systems operational</div>
        </div>

        <div class="nav-section">
            <div class="nav-label">Navigation</div>
            <a class="nav-item active" onclick="showTab('files')"><i class="bi bi-folder2-open"></i> Files</a>
            <a class="nav-item" onclick="showTab('upload')"><i class="bi bi-cloud-upload"></i> Upload</a>
            <a class="nav-item" onclick="showTab('stats')"><i class="bi bi-bar-chart-line"></i> Analytics</a>
        </div>

        <div class="nav-section">
            <div class="nav-label">Filter by Type</div>
            <a class="nav-item" onclick="filterByType('all')"><i class="bi bi-grid-3x3-gap"></i> All Files</a>
            <a class="nav-item" onclick="filterByType('image')"><i class="bi bi-image"></i> Images</a>
            <a class="nav-item" onclick="filterByType('document')"><i class="bi bi-file-text"></i> Documents</a>
            <a class="nav-item" onclick="filterByType('video')"><i class="bi bi-camera-video"></i> Videos</a>
            <a class="nav-item" onclick="filterByType('archive')"><i class="bi bi-file-zip"></i> Archives</a>
        </div>

        <div class="sidebar-stats" id="sidebarStats">
            <div class="stat-pill"><span class="stat-pill-label">Total Files</span><span class="stat-pill-value" id="sbTotalFiles">—</span></div>
            <div class="stat-pill"><span class="stat-pill-label">Total Size</span><span class="stat-pill-value" id="sbTotalSize">—</span></div>
        </div>
    </aside>

    <!-- MAIN -->
    <div class="main">
        <!-- TOPBAR -->
        <div class="topbar">
            <button class="menu-btn" id="menuBtn" onclick="toggleSidebar()"><i class="bi bi-list"></i></button>
            <div class="page-title">File Manager</div>

            <div class="search-wrap">
                <i class="bi bi-search"></i>
                <input class="search-input" type="text" id="searchInput" placeholder="Search files..." oninput="filterFiles()">
            </div>

            <div class="filter-btns">
                <button class="filter-btn active" onclick="setFilter('all', this)">All</button>
                <button class="filter-btn" onclick="setFilter('image', this)">Images</button>
                <button class="filter-btn" onclick="setFilter('document', this)">Docs</button>
                <button class="filter-btn" onclick="setFilter('video', this)">Video</button>
                <button class="filter-btn" onclick="setFilter('archive', this)">Archives</button>
            </div>

            <button class="btn btn-ghost" onclick="refreshFiles()" title="Refresh">
                <i class="bi bi-arrow-clockwise"></i>
            </button>
        </div>

        <!-- CONTENT -->
        <div class="content">

            <!-- TAB: FILES -->
            <div id="tab-files">
                <!-- Stats Row -->
                <div class="stats-grid" id="statsGrid">
                    <div class="stat-card">
                        <div class="stat-num" id="statTotal">—</div>
                        <div class="stat-desc">Total Files</div>
                        <i class="bi bi-files stat-icon"></i>
                    </div>
                    <div class="stat-card">
                        <div class="stat-num" id="statSize">—</div>
                        <div class="stat-desc">Storage Used</div>
                        <i class="bi bi-hdd stat-icon"></i>
                    </div>
                    <div class="stat-card">
                        <div class="stat-num" id="statImages">—</div>
                        <div class="stat-desc">Images</div>
                        <i class="bi bi-image stat-icon"></i>
                    </div>
                    <div class="stat-card">
                        <div class="stat-num" id="statDocs">—</div>
                        <div class="stat-desc">Documents</div>
                        <i class="bi bi-file-text stat-icon"></i>
                    </div>
                </div>

                <div class="files-header">
                    <div style="font-size:0.85rem; color: var(--muted);" id="fileCount">Loading files…</div>
                    <div class="view-toggle">
                        <button class="view-btn active" id="viewList" onclick="setView('list')"><i class="bi bi-list-ul"></i></button>
                        <button class="view-btn" id="viewGrid" onclick="setView('grid')"><i class="bi bi-grid-3x3-gap-fill"></i></button>
                    </div>
                </div>

                <div id="filesContainer"></div>
            </div>

            <!-- TAB: UPLOAD -->
            <div id="tab-upload" style="display:none">
                <div class="upload-zone" id="uploadArea"
                     ondrop="handleDrop(event)"
                     ondragover="handleDragOver(event)"
                     ondragleave="handleDragLeave(event)"
                     onclick="document.getElementById('fileInput').click()">
                    <i class="bi bi-cloud-arrow-up upload-zone-icon"></i>
                    <h3>Drop files here to upload</h3>
                    <p>or click to browse your device</p>
                    <input type="file" id="fileInput" multiple onchange="handleFileSelect(event)">
                </div>

                <div class="progress-list" id="progressList"></div>

                <button class="btn btn-primary btn-upload" id="uploadBtn" onclick="uploadFiles()" style="display:none">
                    <i class="bi bi-upload"></i> Upload Files
                </button>
            </div>

            <!-- TAB: STATS -->
            <div id="tab-stats" style="display:none">
                <div class="stats-grid" style="grid-template-columns: repeat(2,1fr); gap:20px">
                    <div class="stat-card" style="grid-column:span 2">
                        <div style="font-family:var(--font-head);font-size:1rem;font-weight:700;margin-bottom:16px">File Type Breakdown</div>
                        <div id="typeBreakdown"></div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-num" id="s2Total">—</div>
                        <div class="stat-desc">Total Files Stored</div>
                        <i class="bi bi-files stat-icon"></i>
                    </div>
                    <div class="stat-card">
                        <div class="stat-num" id="s2Size">—</div>
                        <div class="stat-desc">Storage Used</div>
                        <i class="bi bi-hdd stat-icon"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- PREVIEW MODAL -->
<div class="modal-backdrop" id="previewModal">
    <div class="modal">
        <div class="modal-header">
            <div class="file-type-icon" id="previewTypeIcon"></div>
            <div class="modal-title" id="previewTitle">File Preview</div>
            <button class="btn btn-ghost" onclick="closeModal('previewModal')" style="padding:6px 10px"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body" id="previewBody"></div>
        <div class="modal-footer">
            <a class="btn btn-primary" id="previewDownloadBtn" href="#" download><i class="bi bi-download"></i> Download</a>
            <button class="btn btn-ghost" onclick="openShareModal(currentPreviewFile)"><i class="bi bi-share"></i> Share</button>
            <button class="btn btn-ghost" style="margin-left:auto" onclick="closeModal('previewModal')">Close</button>
        </div>
    </div>
</div>

<!-- SHARE MODAL -->
<div class="modal-backdrop" id="shareModal">
    <div class="modal" style="max-width:480px">
        <div class="modal-header">
            <div class="modal-title">Share File</div>
            <button class="btn btn-ghost" onclick="closeModal('shareModal')" style="padding:6px 10px"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="modal-body">
            <p style="font-size:0.82rem;color:var(--muted);margin-bottom:16px">Generate a temporary public link for this file.</p>
            <div style="font-size:0.78rem;color:var(--muted);margin-bottom:8px">Link Expiry</div>
            <div class="expiry-opts">
                <div class="expiry-opt sel" onclick="selectExpiry(1, this)">1 Hour</div>
                <div class="expiry-opt" onclick="selectExpiry(24, this)">24 Hours</div>
                <div class="expiry-opt" onclick="selectExpiry(168, this)">7 Days</div>
                <div class="expiry-opt" onclick="selectExpiry(720, this)">30 Days</div>
            </div>
            <div class="share-link-box" id="shareLinkBox" style="display:none">
                <i class="bi bi-link-45deg" style="color:var(--accent)"></i>
                <div class="share-link-url" id="shareLinkUrl"></div>
                <button class="btn btn-icon" onclick="copyShareLink()"><i class="bi bi-clipboard"></i></button>
            </div>
            <button class="btn btn-primary" onclick="generateShareLink()" style="width:100%;justify-content:center">
                <i class="bi bi-link"></i> Generate Link
            </button>
        </div>
    </div>
</div>

<!-- TOAST CONTAINER -->
<div class="toast-wrap" id="toastWrap"></div>

<script>
let allFiles = [];
let currentView = 'list';
let currentFilter = 'all';
let currentSearchQ = '';
let currentShareFile = '';
let currentExpiryHours = 1;
let currentPreviewFile = '';
let selectedFiles = [];

// ---- INIT ----
refreshFiles();

// ---- TABS ----
function showTab(tab) {
    ['files','upload','stats'].forEach(t => {
        document.getElementById('tab-' + t).style.display = t === tab ? 'block' : 'none';
    });
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    event.target.closest('.nav-item').classList.add('active');
    if (tab === 'stats') renderStats();
}

// ---- SIDEBAR MOBILE ----
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('sidebarOverlay').classList.toggle('show');
}

// ---- VIEW ----
function setView(v) {
    currentView = v;
    document.getElementById('viewList').classList.toggle('active', v === 'list');
    document.getElementById('viewGrid').classList.toggle('active', v === 'grid');
    renderFiles();
}

// ---- FILTER ----
function setFilter(type, btn) {
    currentFilter = type;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    renderFiles();
}

function filterByType(type) {
    currentFilter = type;
    document.querySelectorAll('.filter-btn').forEach(b => {
        b.classList.toggle('active', b.textContent.toLowerCase().includes(type === 'all' ? 'all' : type));
    });
    showTab('files');
    renderFiles();
}

function filterFiles() {
    currentSearchQ = document.getElementById('searchInput').value.toLowerCase();
    renderFiles();
}

// ---- FILE TYPE UTILS ----
function getFileCategory(name) {
    const ext = name.split('.').pop().toLowerCase();
    if (['jpg','jpeg','png','gif','webp','svg','bmp','ico'].includes(ext)) return 'image';
    if (['pdf','doc','docx','xls','xlsx','ppt','pptx','txt','md','csv'].includes(ext)) return 'document';
    if (['mp4','mov','avi','mkv','webm','flv'].includes(ext)) return 'video';
    if (['zip','tar','gz','rar','7z','bz2'].includes(ext)) return 'archive';
    return 'other';
}

function getFileIcon(name) {
    const cat = getFileCategory(name);
    const icons = { image: ['bi-image','icon-img'], document: ['bi-file-earmark-text','icon-doc'], video: ['bi-camera-video','icon-vid'], archive: ['bi-file-zip','icon-zip'], other: ['bi-file-earmark','icon-default'] };
    const ext = name.split('.').pop().toLowerCase();
    if (ext === 'pdf') return ['bi-file-earmark-pdf','icon-pdf'];
    return icons[cat] || icons.other;
}

function formatBytes(bytes) {
    if (!bytes) return '—';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB';
    return (bytes/(1024*1024)).toFixed(1) + ' MB';
}

// ---- REFRESH ----
function refreshFiles() {
    fetch('/files')
        .then(r => r.json())
        .then(raw => {
            // Normalize: handle both string[] and object[] from the API
            allFiles = raw.map(f =>
                typeof f === 'string'
                    ? { name: f, size: 0, last_modified: null, content_type: null }
                    : f
            );
            renderFiles();
            updateSidebarStats();
            updateDashStats();
        })
        .catch(e => { console.error('refreshFiles error:', e); showToast('Failed to load files', 'error'); });
}

function updateSidebarStats() {
    const total = allFiles.length;
    const size = allFiles.reduce((s, f) => s + (f.size || 0), 0);
    document.getElementById('sbTotalFiles').textContent = total;
    document.getElementById('sbTotalSize').textContent = formatBytes(size);
}

function updateDashStats() {
    const total = allFiles.length;
    const size = allFiles.reduce((s, f) => s + (f.size || 0), 0);
    const images = allFiles.filter(f => getFileCategory(f.name) === 'image').length;
    const docs = allFiles.filter(f => getFileCategory(f.name) === 'document').length;
    document.getElementById('statTotal').textContent = total;
    document.getElementById('statSize').textContent = formatBytes(size);
    document.getElementById('statImages').textContent = images;
    document.getElementById('statDocs').textContent = docs;
}

// ---- RENDER FILES ----
function renderFiles() {
    let files = allFiles;

    if (currentFilter !== 'all') {
        files = files.filter(f => getFileCategory(f.name) === currentFilter);
    }

    if (currentSearchQ) {
        files = files.filter(f => f.name.toLowerCase().includes(currentSearchQ));
    }

    const container = document.getElementById('filesContainer');
    document.getElementById('fileCount').textContent = `${files.length} file${files.length !== 1 ? 's' : ''}`;

    if (files.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-inbox"></i>
                <h3>No files found</h3>
                <p>${currentSearchQ ? 'Try a different search term.' : 'Upload some files to get started.'}</p>
            </div>`;
        return;
    }

    if (currentView === 'grid') {
        container.innerHTML = `<div class="file-grid">${files.map(f => renderGridCard(f)).join('')}</div>`;
    } else {
        container.innerHTML = `
            <div class="file-table-wrap">
                <table class="file-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Size</th>
                            <th>Modified</th>
                            <th>Type</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>${files.map(f => renderTableRow(f)).join('')}</tbody>
                </table>
            </div>`;
    }
}

function renderTableRow(f) {
    const [iconClass, iconBg] = getFileIcon(f.name);
    const date = f.last_modified ? new Date(f.last_modified).toLocaleDateString() : '—';
    const cat = getFileCategory(f.name);
    return `
        <tr>
            <td>
                <div class="file-name-cell">
                    <div class="file-type-icon ${iconBg}"><i class="bi ${iconClass}"></i></div>
                    <div>
                        <div class="file-name-text">${escHtml(f.name)}</div>
                        <div class="file-size-text" style="font-size:0.72rem">${formatBytes(f.size)}</div>
                    </div>
                </div>
            </td>
            <td class="file-size-text">${formatBytes(f.size)}</td>
            <td class="file-date-text">${date}</td>
            <td><span style="font-size:0.72rem;padding:3px 8px;background:var(--surface2);border-radius:4px;color:var(--muted)">${cat}</span></td>
            <td>
                <div class="action-btns">
                    <button class="btn btn-icon" onclick="openPreview('${escAttr(f.name)}')" title="Preview"><i class="bi bi-eye"></i></button>
                    <a class="btn btn-icon" href="/download?name=${encodeURIComponent(f.name)}" download="${escAttr(f.name)}" title="Download"><i class="bi bi-download"></i></a>
                    <button class="btn btn-icon" onclick="openShareModal('${escAttr(f.name)}')" title="Share"><i class="bi bi-share"></i></button>
                    <button class="btn btn-danger-sm" onclick="deleteFile('${escAttr(f.name)}')" title="Delete"><i class="bi bi-trash"></i></button>
                </div>
            </td>
        </tr>`;
}

function renderGridCard(f) {
    const [iconClass, iconBg] = getFileIcon(f.name);
    return `
        <div class="file-grid-card" onclick="openPreview('${escAttr(f.name)}')">
            <div class="file-grid-actions" onclick="event.stopPropagation()">
                <button class="mini-btn" onclick="openShareModal('${escAttr(f.name)}')" title="Share"><i class="bi bi-share"></i></button>
                <a class="mini-btn" href="/download?name=${encodeURIComponent(f.name)}" download title="Download" onclick="event.stopPropagation()"><i class="bi bi-download"></i></a>
                <button class="mini-btn danger" onclick="deleteFile('${escAttr(f.name)}')" title="Delete"><i class="bi bi-trash"></i></button>
            </div>
            <div class="file-grid-icon ${iconBg}"><i class="bi ${iconClass}"></i></div>
            <div class="file-grid-name">${escHtml(f.name)}</div>
            <div class="file-grid-meta">${formatBytes(f.size)}</div>
        </div>`;
}

// ---- PREVIEW ----
function openPreview(name) {
    currentPreviewFile = name;
    const [iconClass, iconBg] = getFileIcon(name);
    document.getElementById('previewTitle').textContent = name;
    document.getElementById('previewTypeIcon').className = `file-type-icon ${iconBg}`;
    document.getElementById('previewTypeIcon').innerHTML = `<i class="bi ${iconClass}"></i>`;
    document.getElementById('previewDownloadBtn').href = `/download?name=${encodeURIComponent(name)}`;
    document.getElementById('previewDownloadBtn').setAttribute('download', name);

    const body = document.getElementById('previewBody');
    body.innerHTML = '<div style="text-align:center;padding:40px;color:var(--muted)"><i class="bi bi-hourglass-split" style="font-size:2rem"></i><p style="margin-top:10px">Loading preview…</p></div>';

    document.getElementById('previewModal').classList.add('show');

    const ext = name.split('.').pop().toLowerCase();
    const imgExts = ['jpg','jpeg','png','gif','webp','svg','bmp','ico'];
    const txtExts = ['txt','md','csv','json','xml','html','css','js','py','sh','log'];

    if (imgExts.includes(ext)) {
        body.innerHTML = `<img class="preview-img" src="/preview?name=${encodeURIComponent(name)}" alt="${escHtml(name)}" onerror="this.parentElement.innerHTML='<div class=\\'preview-unsupported\\'><i class=\\'bi bi-exclamation-circle\\'></i>Could not load image.</div>'">`;
    } else if (ext === 'pdf') {
        body.innerHTML = `<iframe class="preview-pdf" src="/preview?name=${encodeURIComponent(name)}"></iframe>`;
    } else if (txtExts.includes(ext)) {
        fetch(`/preview-text?name=${encodeURIComponent(name)}`)
            .then(r => r.text())
            .then(txt => {
                body.innerHTML = `<pre class="preview-text">${escHtml(txt)}</pre>`;
            })
            .catch(() => { body.innerHTML = previewUnsupported(); });
    } else {
        body.innerHTML = previewUnsupported(ext);
    }
}

function previewUnsupported(ext) {
    return `<div class="preview-unsupported"><i class="bi bi-file-earmark-x"></i><p>Preview not available for .${ext || 'this'} files.</p><p style="margin-top:8px;font-size:0.78rem">Download the file to view it.</p></div>`;
}

// ---- SHARE ----
function openShareModal(name) {
    currentShareFile = name;
    currentExpiryHours = 1;
    document.querySelectorAll('.expiry-opt').forEach((el, i) => el.classList.toggle('sel', i === 0));
    document.getElementById('shareLinkBox').style.display = 'none';
    document.getElementById('shareModal').classList.add('show');
}

function selectExpiry(hours, el) {
    currentExpiryHours = hours;
    document.querySelectorAll('.expiry-opt').forEach(e => e.classList.remove('sel'));
    el.classList.add('sel');
}

function generateShareLink() {
    fetch(`/share?name=${encodeURIComponent(currentShareFile)}&hours=${currentExpiryHours}`)
        .then(r => r.json())
        .then(d => {
            if (d.url) {
                document.getElementById('shareLinkUrl').textContent = d.url;
                document.getElementById('shareLinkBox').style.display = 'flex';
                showToast('Share link generated', 'success');
            } else {
                showToast(d.error || 'Could not generate link', 'error');
            }
        })
        .catch(() => showToast('Error generating link', 'error'));
}

function copyShareLink() {
    const url = document.getElementById('shareLinkUrl').textContent;
    navigator.clipboard.writeText(url).then(() => showToast('Link copied to clipboard', 'success'));
}

// ---- UPLOAD ----
let dragOverTimeout;
function handleDragOver(e) {
    e.preventDefault();
    document.getElementById('uploadArea').classList.add('dragover');
}
function handleDragLeave(e) {
    document.getElementById('uploadArea').classList.remove('dragover');
}
function handleDrop(e) {
    e.preventDefault();
    document.getElementById('uploadArea').classList.remove('dragover');
    selectedFiles = Array.from(e.dataTransfer.files);
    onFilesSelected();
}
function handleFileSelect(e) {
    selectedFiles = Array.from(e.target.files);
    onFilesSelected();
}
function onFilesSelected() {
    if (!selectedFiles.length) return;
    document.getElementById('uploadArea').querySelector('h3').textContent = `${selectedFiles.length} file(s) selected`;
    document.getElementById('uploadBtn').style.display = 'flex';
}

function uploadFiles() {
    if (!selectedFiles.length) return;
    const list = document.getElementById('progressList');

    selectedFiles.forEach(file => {
        const id = 'p_' + Math.random().toString(36).slice(2);
        list.insertAdjacentHTML('beforeend', `
            <div class="progress-item" id="${id}">
                <div class="progress-header">
                    <span class="progress-name">${escHtml(file.name)}</span>
                    <span class="progress-pct" id="${id}_pct">0%</span>
                </div>
                <div class="progress-bar-bg"><div class="progress-bar-fill" id="${id}_bar" style="width:0%"></div></div>
            </div>`);

        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload');

        xhr.upload.onprogress = e => {
            if (e.lengthComputable) {
                const pct = Math.round(e.loaded / e.total * 100);
                document.getElementById(id + '_pct').textContent = pct + '%';
                document.getElementById(id + '_bar').style.width = pct + '%';
            }
        };

        xhr.onload = () => {
            const bar = document.getElementById(id + '_bar');
            const pct = document.getElementById(id + '_pct');
            if (xhr.status === 200) {
                bar.classList.add('done');
                pct.textContent = '✓';
                pct.style.color = 'var(--accent3)';
                showToast(`${file.name} uploaded`, 'success');
                refreshFiles();
            } else {
                bar.classList.add('error');
                pct.textContent = '✗';
                pct.style.color = 'var(--danger)';
                showToast(`Failed: ${file.name}`, 'error');
            }
        };

        xhr.onerror = () => {
            document.getElementById(id + '_bar').classList.add('error');
            showToast(`Error uploading ${file.name}`, 'error');
        };

        xhr.send(formData);
    });

    selectedFiles = [];
    document.getElementById('uploadBtn').style.display = 'none';
}

// ---- DELETE ----
function deleteFile(name) {
    if (!confirm(`Delete "${name}"?`)) return;
    fetch('/delete?name=' + encodeURIComponent(name), { method: 'DELETE' })
        .then(r => r.json())
        .then(() => { refreshFiles(); showToast(`${name} deleted`, 'success'); })
        .catch(() => showToast('Error deleting file', 'error'));
}

// ---- STATS ----
function renderStats() {
    const cats = { image:0, document:0, video:0, archive:0, other:0 };
    allFiles.forEach(f => { const c = getFileCategory(f.name); cats[c] = (cats[c]||0)+1; });
    const total = allFiles.length || 1;
    const size = allFiles.reduce((s,f) => s+(f.size||0), 0);

    const colors = { image: 'var(--accent)', document: 'var(--accent3)', video: 'orange', archive: '#ffd166', other: 'var(--muted)' };
    let html = '';
    Object.entries(cats).forEach(([cat, count]) => {
        if (!count) return;
        const pct = Math.round(count/total*100);
        html += `
            <div style="margin-bottom:14px">
                <div style="display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:5px">
                    <span style="color:var(--text);text-transform:capitalize">${cat}</span>
                    <span style="color:var(--muted)">${count} files — ${pct}%</span>
                </div>
                <div style="height:6px;background:var(--border);border-radius:4px;overflow:hidden">
                    <div style="height:100%;width:${pct}%;background:${colors[cat]};border-radius:4px;transition:width 0.5s"></div>
                </div>
            </div>`;
    });

    document.getElementById('typeBreakdown').innerHTML = html || '<p style="color:var(--muted);font-size:0.82rem">No files yet.</p>';
    document.getElementById('s2Total').textContent = allFiles.length;
    document.getElementById('s2Size').textContent = formatBytes(size);
}

// ---- MODAL ----
function closeModal(id) { document.getElementById(id).classList.remove('show'); }
document.querySelectorAll('.modal-backdrop').forEach(m => m.addEventListener('click', e => { if (e.target === m) m.classList.remove('show'); }));

// ---- TOAST ----
function showToast(msg, type = 'info') {
    const icons = { success: 'bi-check-circle-fill', error: 'bi-x-circle-fill', info: 'bi-info-circle-fill' };
    const wrap = document.getElementById('toastWrap');
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `<i class="bi ${icons[type]}"></i>${escHtml(msg)}`;
    wrap.appendChild(el);
    setTimeout(() => el.remove(), 3500);
}

// ---- UTILS ----
function escHtml(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function escAttr(s) { return String(s).replace(/'/g,"\\'").replace(/"/g,'&quot;'); }
</script>
</body>
</html>
'''

def get_blob_service():
    if not STORAGE_CONNECTION_STRING:
        return None
    return BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)

def get_container():
    svc = get_blob_service()
    if not svc:
        return None
    return svc.get_container_client(CONTAINER_NAME)

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'av-vault'})

@app.route('/files', methods=['GET'])
def list_files():
    try:
        container = get_container()
        if not container:
            return jsonify([])
        result = []
        for blob in container.list_blobs():
            try:
                size = blob.size or 0
            except Exception:
                size = 0
            try:
                last_modified = blob.last_modified.isoformat() if blob.last_modified else None
            except Exception:
                last_modified = None
            result.append({
                'name': blob.name,
                'size': size,
                'last_modified': last_modified,
                'content_type': None,
            })
        result.sort(key=lambda x: x.get('last_modified') or '', reverse=True)
        return jsonify(result)
    except Exception as e:
        print(f"ERROR /files: {e}")
        return jsonify([]), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        container = get_container()
        if not container:
            return jsonify({'message': 'Storage not configured'}), 400
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        container.upload_blob(file.filename, file.read(), overwrite=True)
        return jsonify({'message': f'✓ {file.filename} uploaded successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete', methods=['DELETE'])
def delete_file():
    try:
        container = get_container()
        if not container:
            return jsonify({'message': 'Storage not configured'}), 400
        name = request.args.get('name')
        if not name:
            return jsonify({'error': 'No file name provided'}), 400
        container.delete_blob(name)
        return jsonify({'message': f'✓ {name} deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['GET'])
def download_file():
    """Stream file download from blob storage."""
    from flask import Response, stream_with_context
    try:
        container = get_container()
        if not container:
            return jsonify({'error': 'Storage not configured'}), 400
        name = request.args.get('name')
        if not name:
            return jsonify({'error': 'No file name provided'}), 400

        blob_client = container.get_blob_client(name)
        download = blob_client.download_blob()
        props = blob_client.get_blob_properties()
        content_type = props.content_settings.content_type or 'application/octet-stream'

        def generate():
            for chunk in download.chunks():
                yield chunk

        response = Response(
            stream_with_context(generate()),
            content_type=content_type
        )
        response.headers['Content-Disposition'] = f'attachment; filename="{name}"'
        if props.size:
            response.headers['Content-Length'] = str(props.size)
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preview', methods=['GET'])
def preview_file():
    """Serve file inline for browser preview (images, PDFs)."""
    from flask import Response, stream_with_context
    try:
        container = get_container()
        if not container:
            return jsonify({'error': 'Storage not configured'}), 400
        name = request.args.get('name')
        if not name:
            return jsonify({'error': 'No file name provided'}), 400

        blob_client = container.get_blob_client(name)
        download = blob_client.download_blob()
        props = blob_client.get_blob_properties()
        content_type = props.content_settings.content_type or 'application/octet-stream'

        def generate():
            for chunk in download.chunks():
                yield chunk

        response = Response(stream_with_context(generate()), content_type=content_type)
        response.headers['Content-Disposition'] = f'inline; filename="{name}"'
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preview-text', methods=['GET'])
def preview_text():
    """Return raw text content for text file previews."""
    try:
        container = get_container()
        if not container:
            return '', 400
        name = request.args.get('name')
        if not name:
            return '', 400

        blob_client = container.get_blob_client(name)
        data = blob_client.download_blob().readall()
        # Limit to 50KB for preview
        text = data[:50_000].decode('utf-8', errors='replace')
        if len(data) > 50_000:
            text += '\n\n… (file truncated for preview)'
        return text, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        return str(e), 500

@app.route('/share', methods=['GET'])
def share_file():
    """Generate a SAS URL for temporary public access."""
    try:
        if not STORAGE_CONNECTION_STRING or not STORAGE_ACCOUNT_KEY or not STORAGE_ACCOUNT_NAME:
            return jsonify({'error': 'Storage account key/name not configured for SAS generation. Set STORAGE_ACCOUNT_KEY and STORAGE_ACCOUNT_NAME in .env.'}), 400

        name = request.args.get('name')
        hours = int(request.args.get('hours', 1))
        if not name:
            return jsonify({'error': 'No file name provided'}), 400

        expiry = datetime.now(timezone.utc) + timedelta(hours=hours)
        sas_token = generate_blob_sas(
            account_name=STORAGE_ACCOUNT_NAME,
            container_name=CONTAINER_NAME,
            blob_name=name,
            account_key=STORAGE_ACCOUNT_KEY,
            permission=BlobSasPermissions(read=True),
            expiry=expiry
        )
        url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{name}?{sas_token}"
        return jsonify({'url': url, 'expires': expiry.isoformat()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
