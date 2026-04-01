import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import StockData from './components/StockData';
import OtherDomain from './components/OtherDomain';

const App = () => {
  return (
    <Router>
      <Switch>
        <Route path='/' exact component={Dashboard} />
        <Route path='/stock-data' component={StockData} />
        <Route path='/other-domain' component={OtherDomain} />
      </Switch>
    </Router>
  );
}

export default App;