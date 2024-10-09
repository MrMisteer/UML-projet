import Vue from 'vue';
import App from '../src/App.vue';
import Toast from 'vue-toastification';
import 'vue-toastification/dist/index.css';

Vue.config.productionTip = false;


Vue.use(Toast);

new Vue({
  render: h => h(App),
}).$mount('#app');
