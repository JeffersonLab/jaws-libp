const repo = 'jeffersonlab/jaws-libp';
const url = 'https://api.github.com/repos/' + repo + '/contents/?ref=gh-pages';

const list = document.getElementById('dirlist');


function addToList(obj) {
  //console.log('addToList', obj);

  const li = document.createElement("li");
  const a = document.createElement("a");
  a.href = obj.name;
  a.innerText = obj.name;
  li.appendChild(a);
  list.appendChild(li);
  
}

async function fetchData() {
    //console.log('fetchData', url);


    const response = await fetch(url);

    const data = await response.json();

    //console.log(data);

    let dirs = data.filter(function(obj) {
       return obj.type === 'dir';
    });

    
    dirs.sort((a, b) => a.name < b.name ? 1 : -1);


    dirs.forEach(addToList);    
    
}

fetchData();
