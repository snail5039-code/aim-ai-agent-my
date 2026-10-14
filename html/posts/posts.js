const API_URL = "https://jsonplaceholder.typicode.com/posts";
const titleButton = document.querySelector("#title-button");
const loadButton = document.querySelector("#load-button");
const message = document.querySelector("#message");
const postList = document.querySelector("#post-list");

function changeTitle() {
  document.querySelector(".post .title").textContent = "JavaScript로 바꾼 제목";
  message.textContent = "첫 글의 제목을 변경했습니다.";
}

function createPost(post, index) {
  const item = document.createElement("li");
  item.id = `post-${post.id}`;
  item.className = "post";

  const title = document.createElement("a");
  title.className = index === 0 ? "title featured" : "title";
  title.href = `https://jsonplaceholder.typicode.com/posts/${post.id}`;
  title.textContent = post.title;

  const details = document.createElement("div");
  details.className = "details";

  const body = document.createElement("p");
  body.className = "body";
  body.textContent = post.body;

  details.append(body);
  item.append(title, details);
  return item;
}

async function loadPosts() {
  loadButton.disabled = true;
  titleButton.disabled = true;
  message.textContent = "게시글을 불러오는 중입니다.";

  try {
    const response = await fetch(API_URL);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    const posts = data.slice(0, 3);
    postList.replaceChildren(...posts.map(createPost));
    message.textContent = posts.length
      ? `게시글 ${posts.length}개를 표시했습니다.`
      : "표시할 게시글이 없습니다.";
  } catch (error) {
    message.textContent = "게시글을 불러오지 못했습니다. 다시 시도하세요.";
    console.error(error);
  } finally {
    loadButton.disabled = false;
    titleButton.disabled = postList.children.length === 0;
  }
}
