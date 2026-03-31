#include <algorithm>
#include <chrono>
#include <cmath>
#include <iostream>
#include <queue>
#include <random>
#include <vector>
#include <climits>
#include <functional>
#include <fstream>

using namespace std;
using ll = int;

struct Task
{
    int id;
    char type;
    int duration;
    vector<int> dependents;
    vector<int> dependencies;
};

int n, n_vector, n_cube, m;
vector<Task> tasks;
ll sum_duration = 0;
vector<ll> bottom_level, top_level;
vector<int> critical_path;

void compute_levels()
{
    bottom_level.assign(n, 0);
    top_level.assign(n, 0);
    critical_path.assign(n, 0);

    vector<int> deg(n);
    vector<int> order;
    order.reserve(n);

    for (int i = 0; i < n; i++)
    {
        deg[i] = tasks[i].dependents.size();
        if (deg[i] == 0)
        {
            order.push_back(i);
            bottom_level[i] = tasks[i].duration;
        }
    }
    for (size_t h = 0; h < order.size(); h++)
    {
        int u = order[h];
        for (int v : tasks[u].dependencies)
        {
            if (bottom_level[v] < bottom_level[u] + tasks[v].duration)
            {
                bottom_level[v] = bottom_level[u] + tasks[v].duration;
            }
            if (--deg[v] == 0)
                order.push_back(v);
        }
    }

    order.clear();
    for (int i = 0; i < n; i++)
    {
        deg[i] = tasks[i].dependencies.size();
        if (deg[i] == 0)
        {
            order.push_back(i);
            top_level[i] = 0;
        }
    }
    for (size_t h = 0; h < order.size(); h++)
    {
        int u = order[h];
        for (int v : tasks[u].dependents)
        {
            if (top_level[v] < top_level[u] + tasks[u].duration)
            {
                top_level[v] = top_level[u] + tasks[u].duration;
            }
            if (--deg[v] == 0)
                order.push_back(v);
        }
    }

    for (int i = 0; i < n; i++)
    {
        critical_path[i] = top_level[i] + bottom_level[i];
    }
}

ll simulate(const vector<ll> &prio, vector<vector<int>> *sched = nullptr)
{
    vector<int> indeg(n);
    for (int i = 0; i < n; i++)
        indeg[i] = tasks[i].dependencies.size();

    if (sched)
        sched->assign(n_vector + n_cube, vector<int>());

    auto cmp = [&](int a, int b)
    {
        return prio[a] != prio[b] ? prio[a] < prio[b] : critical_path[a] != critical_path[b] ? critical_path[a] < critical_path[b]
                                                                                             : tasks[a].duration > tasks[b].duration; // Prefer longer tasks
    };

    priority_queue<int, vector<int>, decltype(cmp)> rdy_v(cmp), rdy_c(cmp);
    for (int i = 0; i < n; i++)
    {
        if (indeg[i] == 0)
        {
            (tasks[i].type == 'V' ? rdy_v : rdy_c).push(i);
        }
    }

    priority_queue<pair<ll, int>, vector<pair<ll, int>>, greater<>> core_v, core_c;
    for (int i = 0; i < n_vector; i++)
        core_v.emplace(0, i);
    for (int i = 0; i < n_cube; i++)
        core_c.emplace(0, n_vector + i);

    priority_queue<tuple<ll, int, int>, vector<tuple<ll, int, int>>, greater<>> evts;

    int done = 0;
    ll now = 0, ans = 0;

    while (done < n)
    {
        while (!rdy_v.empty() && !core_v.empty())
        {
            auto [at, c] = core_v.top();
            core_v.pop();
            int t = rdy_v.top();
            rdy_v.pop();
            ll start = max(now, at);
            ll fin = start + tasks[t].duration;
            evts.emplace(fin, c, t);
            ans = max(ans, fin);
            if (sched)
                (*sched)[c].push_back(tasks[t].id);
        }

        while (!rdy_c.empty() && !core_c.empty())
        {
            auto [at, c] = core_c.top();
            core_c.pop();
            int t = rdy_c.top();
            rdy_c.pop();
            ll start = max(now, at);
            ll fin = start + tasks[t].duration;
            evts.emplace(fin, c, t);
            ans = max(ans, fin);
            if (sched)
                (*sched)[c].push_back(tasks[t].id);
        }

        if (evts.empty())
            break;

        now = get<0>(evts.top());

        while (!evts.empty() && get<0>(evts.top()) == now)
        {
            auto [tm, c, t] = evts.top();
            evts.pop();
            (c < n_vector ? core_v : core_c).emplace(tm, c);
            done++;

            for (int d : tasks[t].dependents)
            {
                if (--indeg[d] == 0)
                {
                    (tasks[d].type == 'V' ? rdy_v : rdy_c).push(d);
                }
            }
        }
    }
    return ans;
}

void solve(const std::string &inputFile, const std::string &outputDir, const std::string &algo)
{
    auto start = chrono::steady_clock::now();

    // if (!(cin >> n >> n_vector >> n_cube))
    //     return 0;

    std::ifstream input_file(inputFile);

    input_file >> n >> n_vector >> n_cube;

    tasks.resize(n);
    for (int i = 0; i < n; i++)
    {
        tasks[i].id = i + 1;
        input_file >> tasks[i].type >> tasks[i].duration;
        sum_duration += tasks[i].duration;
    }

    input_file >> m;
    for (int i = 0; i < m; i++)
    {
        int u, v;
        input_file >> u >> v;
        u--;
        v--;
        tasks[u].dependents.push_back(v);
        tasks[v].dependencies.push_back(u);
    }

    compute_levels();

    const int POP = 40;
    vector<pair<ll, vector<ll>>> pop;

    auto add = [&](auto gen)
    {
        vector<ll> p(n);
        for (int i = 0; i < n; i++)
            p[i] = gen(i);
        ll t = simulate(p);
        pop.emplace_back(t, std::move(p));
    };

    add([](int i)
        { return bottom_level[i]; });
    add([](int i)
        { return top_level[i]; });
    add([](int i)
        { return critical_path[i]; });
    add([](int i)
        { return tasks[i].duration; });

    if (algo.find("heuristics") != std::string::npos) {
        add([](int i)
            { return bottom_level[i] * 1000 + tasks[i].duration; });
        add([](int i)
            { return critical_path[i] * 500 + tasks[i].duration; });
        add([](int i)
            { return bottom_level[i] * 100 - tasks[i].duration; });
        add([](int i)
            { return top_level[i] * 100 + tasks[i].dependents.size(); });

        double avg_v_cores = n_vector > 0 ? (n * 1.0) / n_vector : 1.0;
        double avg_c_cores = n_cube > 0 ? (n * 1.0) / n_cube : 1.0;

        add([avg_v_cores, avg_c_cores](int i)
            { 
            double factor = (tasks[i].type == 'V') ? avg_v_cores : avg_c_cores;
            return bottom_level[i] * (100 + (int)(factor * 10)); });

        add([](int i)
            { return bottom_level[i] * 1000 / max(1, tasks[i].duration); });

        add([](int i)
            { return critical_path[i] * 1000 / max(1, tasks[i].duration); });

        add([](int i)
            { return bottom_level[i] * 100 + tasks[i].dependencies.size() * 10; });

        add([](int i)
            { return bottom_level[i] * 100 - tasks[i].dependents.size() * 10; });

        add([](int i)
            { return bottom_level[i] * 100 + (i * 917 + 123) % 97; });
    }

    sort(pop.begin(), pop.end());

    ll global_best = pop[0].first;
    vector<ll> global_best_prio = pop[0].second;

    constexpr float GENETIC_TIMEOUT = 3500.0;
    constexpr int GENETIC_ITERS = 8;

    if (algo.find("genetic") != std::string::npos) {
        for (uint64_t seed = 0; seed < GENETIC_ITERS; seed++)
        {
            auto now_time = chrono::steady_clock::now();
            double elapsed = chrono::duration_cast<chrono::milliseconds>(now_time - start).count();
            if (elapsed > GENETIC_TIMEOUT)
                break;

            double time_per_seed = (GENETIC_TIMEOUT - elapsed) / (GENETIC_ITERS - seed);
            auto seed_end = now_time + chrono::milliseconds((int)time_per_seed);

            mt19937_64 rng(seed * 12345 + 42);
            uniform_real_distribution<double> prob(0.0, 1.0);
            uniform_int_distribution<int> task_d(0, n - 1);
            uniform_int_distribution<int> parent_sel(0, 4); // Select from top 5

            vector<pair<ll, vector<ll>>> cur_pop = pop;
            ll best = cur_pop[0].first;
            vector<ll> best_prio = cur_pop[0].second;

            int iterations = 0;
            while (chrono::steady_clock::now() < seed_end)
            {
                iterations++;
                sort(cur_pop.begin(), cur_pop.end());
                if ((int)cur_pop.size() > POP)
                {
                    cur_pop.resize(POP);
                }

                vector<pair<ll, vector<ll>>> new_pop(cur_pop.begin(), cur_pop.begin() + min(5, (int)cur_pop.size()));

                for (int k = 0; k < POP - 5; k++)
                {
                    int p1 = parent_sel(rng);
                    int p2 = parent_sel(rng);
                    while (p2 == p1)
                        p2 = parent_sel(rng);

                    vector<ll> child(n);

                    double alpha = prob(rng) * 0.4 + 0.3; // 0.3-0.7 range
                    for (int i = 0; i < n; i++)
                    {
                        child[i] = (ll)(alpha * cur_pop[p1].second[i] +
                                        (1.0 - alpha) * cur_pop[p2].second[i]);
                    }

                    int mut_count = 1 + rng() % 3;
                    for (int j = 0; j < mut_count; j++)
                    {
                        int i = task_d(rng);
                        int op = rng() % 7;
                        switch (op)
                        {
                        case 0:
                            child[i] += (ll)(rng() % 101) - 50;
                            break;
                        case 1:
                            child[i] = bottom_level[i] * (90 + rng() % 21);
                            break;
                        case 2:
                            child[i] = critical_path[i] * (40 + rng() % 21);
                            break;
                        case 3:
                            child[i] += tasks[i].duration * (rng() % 5);
                            break;
                        case 4:
                            swap(child[i], child[task_d(rng)]);
                            break;
                        case 5:
                            child[i] = child[i] * (85 + rng() % 31) / 100;
                            break;
                        case 6:
                            child[i] += (tasks[i].dependents.size() - tasks[i].dependencies.size()) * 10;
                            break;
                        }
                        if (child[i] < 1)
                            child[i] = 1;
                    }

                    ll t = simulate(child);
                    new_pop.emplace_back(t, std::move(child));
                    if (t < best)
                    {
                        best = t;
                        best_prio = new_pop.back().second;
                    }
                }

                cur_pop = std::move(new_pop);
            }

            if (best < global_best)
            {
                global_best = best;
                global_best_prio = best_prio;
            }
        }
    }

    vector<ll> cur = global_best_prio;
    ll cur_time = global_best;
    mt19937_64 rng_final(123456);
    uniform_real_distribution<double> prob_f(0.0, 1.0);
    uniform_int_distribution<int> task_d_f(0, n - 1);
    uniform_int_distribution<int> change_d(-50, 50);

    constexpr int LOCAL_SEARCH_TIMEOUT = 4800;
    int no_improve = 0;

    if (algo.find("annealing") != std::string::npos) {
        while (true)
        {
            auto now_time = chrono::steady_clock::now();
            double elapsed = chrono::duration_cast<chrono::milliseconds>(now_time - start).count();
            if (elapsed > LOCAL_SEARCH_TIMEOUT)
                break;

            double temp = max(1.0, 100.0 * exp(-elapsed / 1000.0));

            vector<ll> np = cur;

            int changes = 1 + (int)(temp / 20.0);
            for (int c = 0; c < changes; c++)
            {
                int i = task_d_f(rng_final);
                if (prob_f(rng_final) < 0.3)
                {
                    if (prob_f(rng_final) < 0.5)
                    {
                        np[i] = (bottom_level[i] * 100 + critical_path[i] * 50) / max(1, tasks[i].duration);
                    }
                    else
                    {
                        np[i] = bottom_level[i] * (80 + rng_final() % 41);
                    }
                }
                else
                {
                    np[i] += change_d(rng_final) * (1 + (int)temp / 10);
                    if (np[i] < 1)
                        np[i] = 1;
                }
            }

            ll t = simulate(np);

            if (t < cur_time || (temp > 0.1 && prob_f(rng_final) < exp((cur_time - t) / temp)))
            {
                cur = np;
                cur_time = t;
                if (t < global_best)
                {
                    global_best = t;
                    global_best_prio = cur;
                    no_improve = 0;
                }
            }
            else
            {
                no_improve++;
            }

            if (no_improve > 1000)
            {
                cur = global_best_prio;
                for (int i = 0; i < n / 10; i++)
                {
                    int idx = task_d_f(rng_final);
                    cur[idx] += change_d(rng_final) * 10;
                    if (cur[idx] < 1)
                        cur[idx] = 1;
                }
                cur_time = simulate(cur);
                no_improve = 0;
            }
        }
    }

    vector<vector<int>> sched;
    simulate(global_best_prio, &sched);

    std::ofstream output_file(outputDir + "output.txt");
    for (const auto &s : sched)
    {
        output_file << s.size();
        for (int id : s)
            output_file << " " << id;
        output_file << "\n";
    }

    cerr << "Total Duration: " << global_best << endl;
    cerr << "Score: " << (ll)(1e6 * (double)sum_duration / global_best) << endl;
}

int main(int argc, char *argv[])
{
    std::string inputFile = argv[1];
    std::string outputDir = argv[2];
    std::string algorithm = argv[3];
    int workTimeSeconds = std::atoi(argv[4]);

    cerr << inputFile << " " << outputDir << " " << algorithm << " " << workTimeSeconds << "\n";

    // TODO: consider algorithm and workTimeSeconds
    solve(inputFile, outputDir, algorithm);

    return 0;
}
