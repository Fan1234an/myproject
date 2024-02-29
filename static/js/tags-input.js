document.addEventListener('DOMContentLoaded', (event) => {
    const tagsInput = document.getElementById('tags-input');
    const tagsList = document.getElementById('tags-list');
    let tagsArray = []; // 這個陣列將用來存儲標籤

    function updateHiddenInput() {
        document.getElementById('post_list').value = tagsArray.join(',');
    }

    function addTag(text) {
        const tag = document.createElement('span');
        tag.className = 'tag';
        tag.textContent = text;

        const closeBtn = document.createElement('span');
        closeBtn.className = 'close';
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', () => {
            removeTag(text, tag);
        });

        tag.appendChild(closeBtn);
        tagsList.appendChild(tag);
        tagsArray.push(text); // 添加標籤到陣列
        updateHiddenInput(); // 更新隱藏的 input 欄位
    }

    function removeTag(text, tagElement) {
        tagElement.remove(); // 從 DOM 中移除標籤
        tagsArray = tagsArray.filter(tag => tag !== text); // 從陣列中移除標籤
        updateHiddenInput(); // 更新隱藏的 input 欄位
    }

    tagsInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const tagValue = this.value.trim();
            if (tagValue && !tagsArray.includes(tagValue)) { // 確保不添加重複的標籤
                addTag(tagValue);
                this.value = ''; // 清空輸入框
            }
        }
    });

    document.getElementById('post-form').onsubmit = function() {
        // 表單提交時，隱藏的 input 欄位已經更新
        return true; // 繼續提交表單
    };
});
