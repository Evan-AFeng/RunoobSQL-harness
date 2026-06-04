<template>
  <main class="app-shell">
    <section class="workspace" aria-labelledby="page-title">
      <header class="workspace-header">
        <div>
          <p class="eyebrow">RunoobSQL</p>
          <h1 id="page-title">SQLite 问数工作台</h1>
        </div>
        <div class="status-pill" :class="statusClass">
          <component :is="statusIcon" :size="18" aria-hidden="true" />
          <span>{{ statusText }}</span>
        </div>
      </header>

      <div class="work-grid">
        <section class="upload-panel" aria-labelledby="upload-title">
          <div class="panel-heading">
            <h2 id="upload-title">数据库</h2>
            <span>.db / .sqlite / .sqlite3</span>
          </div>

          <label
            class="drop-zone"
            :class="{ dragging: isDragging, ready: selectedFile || importResult }"
            @dragenter.prevent="isDragging = true"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
          >
            <input type="file" accept=".db,.sqlite,.sqlite3" @change="handleFileChange" />
            <Database :size="42" aria-hidden="true" />
            <strong>{{ uploadTitle }}</strong>
            <span>{{ uploadMeta }}</span>
          </label>

          <div class="actions">
            <button type="button" class="secondary-button" :disabled="isBusy" @click="clearWorkspace">
              <X :size="18" aria-hidden="true" />
              <span>清除</span>
            </button>
            <button type="button" class="primary-button" :disabled="!selectedFile || isBusy" @click="submitImport">
              <LoaderCircle v-if="isImporting" class="spin" :size="18" aria-hidden="true" />
              <Upload v-else :size="18" aria-hidden="true" />
              <span>{{ isImporting ? "导入中" : "导入" }}</span>
            </button>
          </div>

          <p v-if="importError" class="message error-message">{{ importError }}</p>
          <p v-else-if="importResult" class="message success-message">已导入 {{ importResult.filename }}</p>

          <form class="question-form" @submit.prevent="submitQuestion">
            <label for="question">问题</label>
            <textarea
              id="question"
              v-model="question"
              rows="4"
              :disabled="!importResult || isQuerying"
              placeholder="例如：预算最高的项目有哪些？"
            />
            <button type="submit" class="primary-button" :disabled="!canAskQuestion">
              <LoaderCircle v-if="isQuerying" class="spin" :size="18" aria-hidden="true" />
              <Send v-else :size="18" aria-hidden="true" />
              <span>{{ isQuerying ? "查询中" : "提问" }}</span>
            </button>
          </form>

          <p v-if="queryError" class="message error-message">{{ queryError }}</p>
          <div v-if="thinkingText || visibleModelText || generatedSql" class="trace-panel">
            <h2>模型思考</h2>
            <code v-if="thinkingText">{{ thinkingText }}</code>
            <h2 v-if="visibleModelText">模型输出</h2>
            <code v-if="visibleModelText">{{ visibleModelText }}</code>
            <h2 v-if="generatedSql">生成的 SQL</h2>
            <code v-if="generatedSql">{{ generatedSql }}</code>
          </div>
        </section>

        <section class="result-panel" aria-labelledby="result-title">
          <div class="panel-heading">
            <h2 id="result-title">结果</h2>
            <span>{{ resultCountText }}</span>
          </div>

          <div v-if="!importResult" class="empty-state">
            <TableProperties :size="40" aria-hidden="true" />
            <span>请先导入 SQLite 数据库</span>
          </div>

          <div v-else class="database-summary">
            <dl class="summary-list">
              <div>
                <dt>数据库 ID</dt>
                <dd>{{ importResult.database_id }}</dd>
              </div>
              <div>
                <dt>路径</dt>
                <dd>{{ importResult.path }}</dd>
              </div>
            </dl>

            <div v-if="queryResult" class="query-result">
              <div class="sql-block">
                <span>SQL</span>
                <code>{{ queryResult.sql }}</code>
              </div>

              <div class="result-table-wrap">
                <table v-if="queryResult.rows.length">
                  <thead>
                    <tr>
                      <th v-for="column in queryResult.columns" :key="column">{{ column }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, rowIndex) in queryResult.rows" :key="rowIndex">
                      <td v-for="column in queryResult.columns" :key="column">{{ row[column] }}</td>
                    </tr>
                  </tbody>
                </table>
                <div v-else class="empty-state compact">
                  <span>SQL 执行成功，无返回行</span>
                </div>
              </div>
            </div>

            <div v-else class="table-list">
              <article v-for="table in importResult.tables" :key="table.name" class="table-card">
                <header>
                  <h3>{{ table.name }}</h3>
                  <span>{{ table.row_count }} 行</span>
                </header>
                <ul>
                  <li v-for="column in table.columns" :key="column.name">
                    <span>{{ column.name }}</span>
                    <code>{{ column.type || "UNKNOWN" }}</code>
                    <BadgeCheck v-if="column.primary_key" :size="16" aria-label="primary key" />
                  </li>
                </ul>
              </article>
            </div>
          </div>
        </section>
      </div>
    </section>
  </main>
</template>

<script setup>
import {
  BadgeCheck,
  CheckCircle2,
  CircleAlert,
  Clock3,
  Database,
  LoaderCircle,
  Send,
  TableProperties,
  Upload,
  X,
} from "@lucide/vue";
import { computed, ref } from "vue";

import { ApiError, importDatabase } from "./api/databases";
import { streamQuestion } from "./api/query";

const selectedFile = ref(null);
const importResult = ref(null);
const queryResult = ref(null);
const thinkingText = ref("");
const visibleModelText = ref("");
const generatedSql = ref("");
const streamBuffer = ref("");
const question = ref("");
const importError = ref("");
const queryError = ref("");
const isDragging = ref(false);
const isImporting = ref(false);
const isQuerying = ref(false);
const closeQueryStream = ref(null);

const isBusy = computed(() => isImporting.value || isQuerying.value);
const canAskQuestion = computed(() => Boolean(importResult.value && question.value.trim() && !isBusy.value));

const uploadTitle = computed(() => selectedFile.value?.name ?? importResult.value?.filename ?? "拖入 SQLite 文件");
const uploadMeta = computed(() => {
  if (selectedFile.value) return formatFileSize(selectedFile.value.size);
  if (importResult.value) return `${importResult.value.tables.length} 张表`;
  return "本地文件";
});

const statusText = computed(() => {
  if (isImporting.value) return "导入中";
  if (isQuerying.value) return "查询中";
  if (importError.value || queryError.value) return "失败";
  if (queryResult.value) return "已返回";
  if (importResult.value) return "可提问";
  return "待导入";
});

const statusClass = computed(() => ({
  pending: !importResult.value && !isBusy.value,
  loading: isBusy.value,
  failed: Boolean(importError.value || queryError.value),
  done: Boolean((importResult.value || queryResult.value) && !importError.value && !queryError.value),
}));

const statusIcon = computed(() => {
  if (isBusy.value) return LoaderCircle;
  if (importError.value || queryError.value) return CircleAlert;
  if (importResult.value || queryResult.value) return CheckCircle2;
  return Clock3;
});

const resultCountText = computed(() => {
  if (queryResult.value) return `${queryResult.value.rows.length} 行`;
  const count = importResult.value?.tables?.length ?? 0;
  return count ? `${count} 张表` : "无数据";
});

function handleFileChange(event) {
  const [file] = event.target.files;
  setSelectedFile(file);
}

function handleDrop(event) {
  isDragging.value = false;
  const [file] = event.dataTransfer.files;
  setSelectedFile(file);
}

function setSelectedFile(file) {
  if (!file) return;
  selectedFile.value = file;
  importError.value = "";
  queryError.value = "";
  importResult.value = null;
  resetQueryState();
}

function clearWorkspace() {
  selectedFile.value = null;
  importResult.value = null;
  question.value = "";
  importError.value = "";
  queryError.value = "";
  closeQueryStream.value?.();
  closeQueryStream.value = null;
  resetQueryState();
}

async function submitImport() {
  if (!selectedFile.value) return;

  isImporting.value = true;
  importError.value = "";
  queryError.value = "";
  resetQueryState();
  try {
    importResult.value = await importDatabase(selectedFile.value);
  } catch (error) {
    importError.value = error instanceof ApiError ? error.message : "导入失败";
  } finally {
    isImporting.value = false;
  }
}

async function submitQuestion() {
  if (!canAskQuestion.value) return;

  isQuerying.value = true;
  queryError.value = "";
  resetQueryState();
  closeQueryStream.value?.();
  closeQueryStream.value = streamQuestion({
    question: question.value,
    databaseId: importResult.value.database_id,
    onEvent: handleStreamEvent,
    onError: handleStreamError,
    onDone: () => {
      isQuerying.value = false;
      closeQueryStream.value = null;
    },
  });
}

function handleStreamEvent(event) {
  if (event.type === "model_delta") {
    appendModelDelta(event.content);
  }
  if (event.type === "sql") {
    generatedSql.value = event.sql;
  }
  if (event.type === "result") {
    queryResult.value = {
      sql: event.sql,
      columns: event.columns,
      rows: event.rows,
    };
  }
}

function handleStreamError(payload) {
  queryError.value = payload?.message ?? "查询失败";
  isQuerying.value = false;
  closeQueryStream.value = null;
}

function appendModelDelta(content) {
  if (!content) return;
  streamBuffer.value += content;
  const parsed = parseThinkStream(streamBuffer.value);
  thinkingText.value = parsed.thinking;
  visibleModelText.value = parsed.visible;
}

function parseThinkStream(text) {
  let cursor = 0;
  let thinking = "";
  let visible = "";
  const lowerText = text.toLowerCase();

  while (cursor < text.length) {
    const openIndex = lowerText.indexOf("<think>", cursor);
    if (openIndex < 0) {
      visible += text.slice(cursor);
      break;
    }

    visible += text.slice(cursor, openIndex);
    const thinkStart = openIndex + "<think>".length;
    const closeIndex = lowerText.indexOf("</think>", thinkStart);
    if (closeIndex < 0) {
      thinking += text.slice(thinkStart);
      break;
    }

    thinking += text.slice(thinkStart, closeIndex);
    cursor = closeIndex + "</think>".length;
  }

  return {
    thinking: thinking.trim(),
    visible: visible.trim(),
  };
}

function resetQueryState() {
  queryResult.value = null;
  thinkingText.value = "";
  visibleModelText.value = "";
  generatedSql.value = "";
  streamBuffer.value = "";
}

function formatFileSize(size) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}
</script>
