CREATE OR REPLACE FUNCTION public.admin_list_users()
RETURNS TABLE (user_id uuid, email text, created_at timestamptz, last_sign_in_at timestamptz, roles text[], status text, project_count bigint)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path TO 'public' AS $$
BEGIN
  IF auth.uid() IS NULL THEN RAISE EXCEPTION 'non authentifié'; END IF;
  IF NOT public.has_permission(auth.uid(), 'users.read') THEN
    PERFORM public.log_admin_action('users.list','users.read',NULL,NULL,
      CASE WHEN public.is_suspended(auth.uid()) THEN 'compte suspendu' ELSE 'permission manquante' END,'denied');
    RAISE EXCEPTION 'accès refusé' USING ERRCODE = '42501';
  END IF;
  PERFORM public.log_admin_action('users.list','users.read',NULL,NULL,NULL,'allowed');
  RETURN QUERY
    SELECT u.id, u.email::text, u.created_at, u.last_sign_in_at,
           COALESCE((SELECT array_agg(r.role::text ORDER BY r.role::text) FROM public.user_roles r WHERE r.user_id = u.id), '{}'),
           COALESCE((SELECT s.status FROM public.account_status s WHERE s.user_id = u.id), 'active'),
           (SELECT count(*) FROM public.projects p WHERE p.user_id = u.id)
    FROM auth.users u
    ORDER BY u.created_at DESC
    LIMIT 500;
END; $$;
REVOKE ALL ON FUNCTION public.admin_list_users() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.admin_list_users() TO authenticated;