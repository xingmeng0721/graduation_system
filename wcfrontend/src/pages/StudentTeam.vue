<template>
  <div class="team-page">
    <h2>我的团队</h2>

```
<!-- 若已加入团队 -->
<div v-if="team">
  <div class="team-info">
    <h3>{{ team.name }}</h3>
    <p>组长：{{ team.leader_name }}</p>

    <h4>成员列表：</h4>
    <ul>
      <li v-for="member in team.members" :key="member.id">{{ member.stu_name }}</li>
    </ul>

    <div class="team-actions">
      <button class="btn btn-danger" @click="leaveTeam">退出团队</button>
    </div>
  </div>
</div>

<!-- 若未加入团队 -->
<div v-else>
  <div class="create-join-section">
    <h3>你还没有加入任何团队</h3>
    <div class="actions">
      <button class="btn btn-primary" @click="createTeam">创建团队</button>

      <div class="join-team">
        <input v-model="joinCode" placeholder="输入邀请码加入团队" />
        <button class="btn btn-success" @click="joinTeam">加入</button>
      </div>
    </div>
  </div>
</div>
```

  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import apiClient from "../plugins/axios";

const team = ref(null);
const joinCode = ref("");

// 加载学生团队信息
const loadTeam = async () => {
  try {
    const res = await apiClient.get("student/team/");
    team.value = res.data;
  } catch (err) {
    team.value = null;
  }
};

// 创建团队
const createTeam = async () => {
  const name = prompt("请输入团队名称：");
  if (!name) return;

  try {
    const res = await apiClient.post("student/team/create/", { name });
    alert("团队创建成功！");
    team.value = res.data;
  } catch (err) {
    alert(err.response?.data?.error || "创建失败");
  }
};

// 加入团队
const joinTeam = async () => {
  if (!joinCode.value) {
    alert("请输入邀请码");
    return;
  }
  try {
    const res = await apiClient.post("student/team/join/", { code: joinCode.value });
    alert("加入成功！");
    team.value = res.data;
  } catch (err) {
    alert(err.response?.data?.error || "加入失败");
  }
};

// 退出团队
const leaveTeam = async () => {
  if (!confirm("确定要退出该团队吗？")) return;

  try {
    await apiClient.post("student/team/leave/");
    alert("已退出团队");
    team.value = null;
  } catch (err) {
    alert(err.response?.data?.error || "退出失败");
  }
};

onMounted(loadTeam);
</script>

<style scoped>
.team-page {
  background: #fff;
  border-radius: 10px;
  padding: 30px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.team-info {
  border: 1px solid #ddd;
  border-radius: 10px;
  padding: 20px;
}

.create-join-section {
  text-align: center;
  margin-top: 40px;
}

.join-team {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 10px;
}

input {
  padding: 8px 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  width: 200px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-primary {
  background-color: #3498db;
  color: white;
}

.btn-success {
  background-color: #2ecc71;
  color: white;
}

.btn-danger {
  background-color: #e74c3c;
  color: white;
}
</style>
